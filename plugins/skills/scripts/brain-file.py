#!/usr/bin/env python3
"""File the notes in a summarizer's final message into the brain vault, then index them.

Usage: brain-file.py [--vault PATH]     (default: $BRAIN_VAULT or ~/Documents/brain)

Stdlib only. Runs as a SubagentStop hook: the hook JSON on stdin carries
`last_assistant_message` and `agent_id`. Notes are delimited blocks in that message:

    <<<NOTE <file-name>.md
    ---
    type: sdd-run
    ...
    ---
    body
    NOTE>>>

Each note needs YAML frontmatter with `type` (sdd-run | decision), `project`, `run`,
and `date`; an sdd-run note also needs `outcome`. Notes are filed to:
  sdd-run  -> projects/<project>/<run>.md   (and one line is added to index.md)
  decision -> decisions/<project>/<file name>

Exit: 0 filed; 2 problems, reasons on stderr so the summarizer re-emits its notes;
1 the vault is missing. A second failure for the same agent is not blocked again: the
faulty notes go to `_rejected/` with a `.reason` file and the exit is 0.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

SAFE = re.compile(r"^[A-Za-z0-9._-]+$")
NOTE = re.compile(r"<<<NOTE (\S+)\n(.*?)\nNOTE>>>", re.DOTALL)
TYPES = ("sdd-run", "decision")
NONE_FOUND = "(message)"


def parse_frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    block = text[4:].split("\n---", 1)[0]
    fields = {}
    for line in block.splitlines():
        key, sep, value = line.partition(":")
        if sep and key.strip():
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def validate(name: str, fields: dict[str, str]) -> str | None:
    if not SAFE.match(name) or not name.endswith(".md"):
        return "file name must match [A-Za-z0-9._-]+ and end in .md"
    required = ["type", "project", "run", "date"]
    if fields.get("type") == "sdd-run":
        required.append("outcome")
    missing = [key for key in required if not fields.get(key)]
    if missing:
        return f"missing frontmatter keys: {', '.join(missing)}"
    if fields["type"] not in TYPES:
        return f"type must be one of {', '.join(TYPES)}"
    for key in ("project", "run"):
        if not SAFE.match(fields[key]):
            return f"`{key}` must match [A-Za-z0-9._-]+"
    return None


def destination(vault: Path, name: str, fields: dict[str, str]) -> Path:
    if fields["type"] == "sdd-run":
        return vault / "projects" / fields["project"] / f"{fields['run']}.md"
    return vault / "decisions" / fields["project"] / name


def add_to_index(vault: Path, fields: dict[str, str]) -> None:
    index = vault / "index.md"
    target = f"projects/{fields['project']}/{fields['run']}"
    existing = index.read_text(encoding="utf-8") if index.exists() else "# Index\n\n"
    if f"[[{target}|" in existing:
        return
    line = f"- {fields['date']} [[{target}|{fields['project']}/{fields['run']}]] — {fields['outcome']}\n"
    index.write_text(existing + line, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--vault", type=Path)
    args = parser.parse_args()
    vault = (args.vault or Path(os.environ.get("BRAIN_VAULT", "~/Documents/brain"))).expanduser()
    if not vault.is_dir():
        print(f"brain-file: vault not found: {vault}", file=sys.stderr)
        return 1

    payload = {}
    if not sys.stdin.isatty():
        try:
            payload = json.load(sys.stdin)
        except json.JSONDecodeError:
            pass
    message = payload.get("last_assistant_message") or ""
    agent_id = str(payload.get("agent_id") or "unknown")
    marker = vault / f".retry-{agent_id if SAFE.match(agent_id) else 'unknown'}"

    problems: dict[str, tuple[str, str]] = {}
    filed = 0
    notes = NOTE.findall(message)
    if not notes:
        problems[NONE_FOUND] = ("no <<<NOTE name.md ... NOTE>>> blocks in the final message", message)
    for name, content in notes:
        fields = parse_frontmatter(content)
        reason = validate(name, fields)
        if reason:
            problems[name] = (reason, content)
            continue
        target = destination(vault, name, fields)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content + "\n", encoding="utf-8")
        if fields["type"] == "sdd-run":
            add_to_index(vault, fields)
        filed += 1

    if not problems:
        marker.unlink(missing_ok=True)
        print(f"brain-file: filed {filed} note(s)")
        return 0
    if not marker.exists():
        marker.write_text("blocked once\n", encoding="utf-8")
        for name, (reason, _) in problems.items():
            print(f"brain-file: {name}: {reason}", file=sys.stderr)
        print("brain-file: re-emit ALL notes as <<<NOTE name.md ... NOTE>>> blocks with valid frontmatter", file=sys.stderr)
        return 2
    marker.unlink()
    rejected = vault / "_rejected"
    rejected.mkdir(exist_ok=True)
    for name, (reason, content) in problems.items():
        stem = re.sub(r"[^A-Za-z0-9._-]", "_", name)
        (rejected / stem).write_text(content + "\n", encoding="utf-8")
        (rejected / f"{stem}.reason").write_text(reason + "\n", encoding="utf-8")
        print(f"brain-file: rejected {name}: {reason}", file=sys.stderr)
    print(f"brain-file: filed {filed} note(s), rejected {len(problems)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
