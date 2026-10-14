#!/usr/bin/env -S uv run --quiet --with pyyaml python
"""Validate a repo's staged brain notes against note schema v3.

Usage:
    ./validate-notes.py <staging-dir> --repo-root <path-to-repo> [--repo-roots name=path ...]

Exits non-zero if any ERROR is found. WARN lines never fail the run.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import yaml

TYPES = {
    "architecture": ("", ["Purpose", "Boundaries", "Entry points", "Data stores",
                          "External dependencies", "Runtime shape"]),
    "context": ("contexts", ["Responsibility", "Aggregates and invariants", "Ports",
                             "Adapters", "Flows", "Nuances"]),
    "module": ("modules", ["Public surface", "Contracts and invariants",
                           "Known implementations", "Extension points", "Nuances"]),
    "component": ("components", ["Responsibility", "Constraints", "Collaborators",
                                 "Flows", "Nuances"]),
    "drift": ("drift", ["Claim in docs", "Reality in code", "Impact"]),
    "decision": ("decisions", ["Decision", "Rationale", "Consequences",
                               "Alternatives rejected"]),
    "gotcha": ("gotchas", ["Symptom", "Cause", "Fix or workaround"]),
    "glossary": ("glossary", ["Definition", "Avoid"]),
    "dependency": ("", ["Consumes", "Consumed by", "Version pins",
                        "Breaking-change blast radius"]),
}

KEY_ORDER = ["type", "repo", "id", "title", "group", "stack", "branch", "commit",
             "date", "updated", "provenance", "sources", "commits", "depends_on",
             "consumed_by", "related", "tags"]
OPTIONAL = {"commits"}

RELATIONS = {"implements", "consumes", "extends", "contradicts", "supersedes",
             "refines", "contains", "part_of"}
PROVENANCE = {"documented", "reconstructed", "mixed"}

# Slugs pinned for the two notes that live at the repo-folder root.
ROOT_SLUGS = {"architecture.md": "overview", "dependencies.md": "map"}

# `[ \t]` not `\s`: `\s` crosses newlines, so prose like "token=\ncurrent_user.token"
# false-positived and forced legitimate sentences to be reworded.
SECRET = re.compile(
    r"(?i)(password|passwd|secret|api[_-]?key|token|authorization)"
    r"[ \t]*[:=][ \t]*['\"]?(?:Bearer[ \t]+|Basic[ \t]+)?[A-Za-z0-9/+_\-]{12,}"
)
RANGE = re.compile(r"^(\d+)-(\d+)$")

errors: list[str] = []
warns: list[str] = []
note_ids: set[str] = set()
wikilinks: list[tuple[str, str]] = []


def commit_exists(repo_root: Path, sha: str) -> bool:
    """True if `sha` resolves to a commit object in repo_root. Read-only."""
    result = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{sha}^{{commit}}"],
        capture_output=True,
    )
    return result.returncode == 0


def err(where: str, msg: str) -> None:
    errors.append(f"ERROR {where}: {msg}")


def warn(where: str, msg: str) -> None:
    warns.append(f"WARN  {where}: {msg}")


def split_front_matter(text: str, where: str) -> tuple[dict | None, str]:
    if not text.startswith("---\n"):
        err(where, "no YAML frontmatter at start of file")
        return None, text
    end = text.find("\n---\n", 3)
    if end == -1:
        err(where, "frontmatter not terminated by a --- line")
        return None, text
    raw = text[4:end + 1]
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        err(where, f"frontmatter is not valid YAML: {exc}")
        return None, text[end + 5:]
    if not isinstance(data, dict):
        err(where, "frontmatter is not a mapping")
        return None, text[end + 5:]
    # key order check needs the raw text, PyYAML sorts nothing but dict() keeps order
    return data, text[end + 5:]


def check_keys(fm: dict, where: str) -> None:
    keys = list(fm)
    missing = [k for k in KEY_ORDER if k not in keys and k not in OPTIONAL]
    if missing:
        err(where, f"missing frontmatter keys: {', '.join(missing)}")
    extra = [k for k in keys if k not in KEY_ORDER]
    if extra:
        warn(where, f"unexpected frontmatter keys: {', '.join(extra)}")
    ordered = [k for k in keys if k in KEY_ORDER]
    if ordered != [k for k in KEY_ORDER if k in ordered]:
        err(where, f"frontmatter key order wrong: {ordered}")


def check_lines(path: Path, spec, where: str, src_label: str) -> None:
    if spec == [] or spec is None:
        return  # cited for existence only
    if not isinstance(spec, list):
        err(where, f"{src_label}: `lines` must be a list of range strings, got {spec!r}")
        return
    try:
        total = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError as exc:
        err(where, f"{src_label}: cannot read file: {exc}")
        return
    for item in spec:
        m = RANGE.match(str(item))
        if not m:
            err(where, f"{src_label}: bad range {item!r}, expected \"start-end\"")
            continue
        start, end = int(m.group(1)), int(m.group(2))
        if start < 1 or start > end:
            err(where, f"{src_label}: nonsensical range {item!r}")
        elif end > total:
            err(where, f"{src_label}: range {item!r} exceeds file length ({total} lines)")


def check_sources(fm: dict, where: str, roots: dict[str, Path], default: Path) -> None:
    sources = fm.get("sources")
    if not isinstance(sources, list) or not sources:
        err(where, "`sources` must be a non-empty list")
        return
    for entry in sources:
        if not isinstance(entry, dict) or "path" not in entry:
            err(where, f"source entry must be a mapping with `path`: {entry!r}")
            continue
        root = default
        if "repo" in entry:
            root = roots.get(entry["repo"], None)
            if root is None:
                # Not a warning: an unverified cross-repo citation is exactly where a bad
                # inbound edge hides, and warnings do not fail the gate.
                err(where, f"source cites repo {entry['repo']!r} but no --repo-roots entry "
                           f"was supplied for it, so the citation is unverified")
                continue
        target = root / entry["path"]
        label = f"sources[{entry['path']}]"
        if not target.exists():
            err(where, f"{label}: path does not exist under {root}")
            continue
        check_lines(target, entry.get("lines"), where, label)


def check_edges(fm: dict, where: str, known: set[str]) -> None:
    # Repos cited as evidence anywhere in this note's sources.
    cited = {s["repo"] for s in (fm.get("sources") or [])
             if isinstance(s, dict) and s.get("repo")}
    for key in ("depends_on", "consumed_by"):
        value = fm.get(key)
        if value is None:
            continue
        if not isinstance(value, list):
            err(where, f"`{key}` must be a list")
            continue
        for entry in value:
            if not isinstance(entry, dict) or "repo" not in entry:
                err(where, f"`{key}` entry must be a mapping with `repo`: {entry!r}")
                continue
            symbols = entry.get("symbols")
            if symbols is not None and not isinstance(symbols, list):
                err(where, f"`{key}` entry for {entry['repo']}: `symbols` must be a list")
            # Repo identity is the repo/folder name everywhere, never the published
            # package name, so a graph join on repo name connects. `observability-lib`
            # publishes `observability`; that belongs in prose, not in an edge.
            if known and entry["repo"] not in known:
                err(where, f"`{key}` names {entry['repo']!r}, which is not a known repo key; "
                           f"use the repository name, not the published package name")
            # An inbound edge asserts a fact about ANOTHER repo, so it must cite that
            # repo's own file. This is the check that catches invented consumers.
            if key == "consumed_by" and entry["repo"] not in cited:
                err(where, f"consumed_by claims {entry['repo']!r} but no `sources` entry "
                           f"cites that repo; an unevidenced inbound edge is not admissible")
    related = fm.get("related")
    if related is None:
        return
    if not isinstance(related, list):
        err(where, "`related` must be a list")
        return
    for entry in related:
        if not isinstance(entry, dict) or "id" not in entry or "relation" not in entry:
            err(where, f"`related` entry needs `id` and `relation`: {entry!r}")
            continue
        if entry["relation"] not in RELATIONS:
            err(where, f"`related` relation {entry['relation']!r} not in {sorted(RELATIONS)}")


def check_body(body: str, headings: list[str], where: str) -> None:
    found = [m.group(1).strip() for m in re.finditer(r"^## (.+)$", body, re.M)]
    if found != headings:
        err(where, f"headings {found} != required {headings}")
        return
    positions = [m.start() for m in re.finditer(r"^## .+$", body, re.M)]
    for i, pos in enumerate(positions):
        end = positions[i + 1] if i + 1 < len(positions) else len(body)
        section = body[pos:end].split("\n", 1)[1].strip()
        if not section:
            err(where, f"section `{headings[i]}` is empty; write `Not recorded` instead")


def check_note(path: Path, staging: Path, roots: dict[str, Path], default: Path,
               known: set[str]) -> None:
    where = str(path.relative_to(staging))
    text = path.read_text(encoding="utf-8")
    fm, body = split_front_matter(text, where)
    if fm is None:
        return
    check_keys(fm, where)

    ntype = fm.get("type")
    if ntype not in TYPES:
        err(where, f"type {ntype!r} not one of {sorted(TYPES)}")
        return
    folder, headings = TYPES[ntype]

    actual_folder = path.parent.name if path.parent != staging else ""
    if actual_folder != folder:
        err(where, f"type {ntype!r} belongs in {folder or '<repo root>'}/, found in {actual_folder or '<repo root>'}/")

    repo = fm.get("repo")
    expected_slug = ROOT_SLUGS.get(path.name, path.stem)
    expected_id = f"{repo}--{ntype}--{expected_slug}"
    if fm.get("id") != expected_id:
        err(where, f"id {fm.get('id')!r} should be {expected_id!r}")
    if fm.get("id") in note_ids:
        err(where, f"duplicate id {fm.get('id')!r}")
    note_ids.add(fm.get("id"))

    if fm.get("provenance") not in PROVENANCE:
        err(where, f"provenance {fm.get('provenance')!r} not in {sorted(PROVENANCE)}")

    tags = fm.get("tags") or []
    for required in (ntype, repo, fm.get("group")):
        if required and required not in tags:
            err(where, f"tags missing {required!r}")

    commits = fm.get("commits")
    if commits is not None:
        if not isinstance(commits, list):
            err(where, "`commits` must be a list of {sha, note} mappings")
        else:
            for entry in commits:
                if not isinstance(entry, dict) or "sha" not in entry:
                    err(where, f"`commits` entry needs a `sha`: {entry!r}")
                elif not re.fullmatch(r"[0-9a-f]{7,40}", str(entry["sha"])):
                    err(where, f"`commits` sha {entry['sha']!r} is not a hex sha")
                elif not commit_exists(default, str(entry["sha"])):
                    err(where, f"`commits` sha {entry['sha']!r} does not exist in {default}")

    check_sources(fm, where, roots, default)
    check_edges(fm, where, known)
    check_body(body, headings, where)

    if SECRET.search(text):
        err(where, "possible secret or credential in note text")
    for m in re.finditer(r"\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", text):
        wikilinks.append((where, m.group(1).strip()))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("staging", type=Path)
    ap.add_argument("--repo-root", type=Path, required=True)
    ap.add_argument("--repo-roots", nargs="*", default=[],
                    help="other repos as name=path, for cross-repo source citations")
    ap.add_argument("--roots-file", type=Path,
                    help="JSON {repo: path} for every repo; simpler than listing them")
    args = ap.parse_args()

    roots = {}
    if args.roots_file:
        roots.update({k: Path(v) for k, v in
                      json.loads(args.roots_file.read_text(encoding="utf-8")).items()})
    for pair in args.repo_roots:
        name, _, value = pair.partition("=")
        roots[name] = Path(value)

    notes = sorted(args.staging.rglob("*.md"))
    if not notes:
        print(f"ERROR: no notes found under {args.staging}")
        return 1
    for note in notes:
        check_note(note, args.staging, roots, args.repo_root, set(roots))

    # wikilinks pointing at this repo's own notes must resolve
    this_repo = args.staging.name
    local = {f"repos/{this_repo}/{p.relative_to(args.staging).with_suffix('')}" for p in notes}
    for where, target in wikilinks:
        if target.startswith(f"repos/{this_repo}/") and target not in local:
            warn(where, f"wikilink {target!r} has no matching note in this repo")

    for line in warns:
        print(line)
    for line in errors:
        print(line)
    print(f"\n{len(notes)} notes checked, {len(errors)} errors, {len(warns)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
