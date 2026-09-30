#!/usr/bin/env python3
"""Deterministic boundary checks for the context-first DDD/hexagonal topology.

Usage: ddd-check.py REPO [--changed-since REF]

Static imports only; no dependencies beyond the standard library. With
--changed-since, only files that differ from REF (working tree included, plus
untracked files) are reported, so pre-existing debt is not blamed on a run.

Output: one `RULE path:line message` per violation, then a SUMMARY line.
Exit: 0 clean, 1 violations, 3 topology (a `bounded_context/` package) not found.
"""

import argparse
import ast
import subprocess
import sys
from pathlib import Path

LAYERS = ("domain", "application", "infrastructure")
FRAMEWORKS = ("fastapi", "starlette", "sqlalchemy", "alembic")
EXCLUDED_DIRS = {".venv", "venv", "node_modules", "__pycache__", ".git"}


def find_root(repo: Path) -> Path | None:
    for candidate in (repo / "src", repo):
        if (candidate / "bounded_context").is_dir():
            return candidate
    return None


def changed_files(repo: Path, ref: str) -> set[Path]:
    def git(*args: str) -> list[str]:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
        )
        return result.stdout.splitlines()

    names = git("diff", "--name-only", "--relative", "--diff-filter=ACMR", ref)
    names += git("ls-files", "--others", "--exclude-standard")
    return {(repo / name).resolve() for name in names}


def locate(module: list[str]) -> tuple[str, str | None, str | None] | None:
    """Return (kind, context, layer) for a module path relative to the source root."""
    if module[0] == "bounded_context" and len(module) >= 3:
        return "context", module[1], module[2] if module[2] in LAYERS else None
    if module[0] == "shared_kernel":
        layer = module[1] if len(module) > 1 and module[1] in LAYERS else None
        return "shared_kernel", None, layer
    if module[0] in ("core", "interfaces"):
        return module[0], None, None
    return None


def target_layer(target: list[str]) -> str | None:
    if target[0] == "bounded_context" and len(target) >= 3 and target[2] in LAYERS:
        return target[2]
    if target[0] == "shared_kernel" and len(target) >= 2 and target[1] in LAYERS:
        return target[1]
    return None


def import_targets(node: ast.AST, package: list[str]) -> list[list[str]]:
    if isinstance(node, ast.Import):
        return [alias.name.split(".") for alias in node.names]
    if not isinstance(node, ast.ImportFrom):
        return []
    if node.level == 0:
        return [node.module.split(".")] if node.module else []
    if node.level - 1 > len(package):
        return []
    base = package[: len(package) - (node.level - 1)]
    if node.module:
        return [base + node.module.split(".")]
    return [base + [alias.name] for alias in node.names]


def violations_for_import(place, target: list[str]) -> list[tuple[str, str]]:
    kind, context, layer = place
    found = []
    top = target[0]
    landing = target_layer(target)
    if kind == "context":
        if layer == "domain":
            if top in FRAMEWORKS:
                found.append(("DDD-DEP-02", f"domain imports framework `{top}`"))
            if landing in ("application", "infrastructure") or top == "interfaces":
                found.append(("DDD-DEP-01", f"domain imports outward layer `{'.'.join(target)}`"))
        if layer == "application" and (landing == "infrastructure" or top == "interfaces"):
            found.append(("DDD-DEP-03", f"application imports outward layer `{'.'.join(target)}`"))
        if top == "bounded_context" and len(target) >= 2 and target[1] != context:
            found.append(("DDD-CTX-01", f"context `{context}` imports context `{target[1]}` internals"))
    if kind == "shared_kernel" and top == "bounded_context":
        found.append(("DDD-CTX-02", "shared_kernel imports a bounded context"))
    if kind == "core" and (
        top in ("fastapi", "starlette", "interfaces") or "infrastructure" in target
    ):
        found.append(("DDD-CORE-01", f"core imports `{'.'.join(target)}`"))
    return found


def check_file(path: Path, root: Path, repo: Path) -> list[str]:
    parts = list(path.relative_to(root).with_suffix("").parts)
    package = parts[:-1]
    module = package if parts[-1] == "__init__" else parts
    place = locate(module) if module else None
    if place is None:
        return []
    shown = path.relative_to(repo)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError as error:
        return [f"DDD-PARSE {shown}:{error.lineno or 0} cannot parse file"]
    out = []
    in_infrastructure = place[2] == "infrastructure"
    for node in ast.walk(tree):
        for target in import_targets(node, package):
            for rule, message in violations_for_import(place, target):
                out.append(f"{rule} {shown}:{node.lineno} {message}")
        if in_infrastructure and isinstance(node, ast.ClassDef) and node.name.endswith("Service"):
            out.append(
                f"DDD-ADP-01 {shown}:{node.lineno} infrastructure class `{node.name}` "
                "must use the `Adapter` suffix, not `Service`"
            )
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path)
    parser.add_argument("--changed-since", metavar="REF")
    args = parser.parse_args()

    repo = args.repo.resolve()
    root = find_root(repo)
    if root is None:
        print("NO_TOPOLOGY no `bounded_context/` package under src/ or the repo root")
        return 3

    only = changed_files(repo, args.changed_since) if args.changed_since else None
    files = [
        path
        for path in sorted(root.rglob("*.py"))
        if not EXCLUDED_DIRS.intersection(path.parts) and (only is None or path.resolve() in only)
    ]
    violations = [line for path in files for line in check_file(path, root, repo)]
    if violations:
        print("\n".join(violations))
    scope = f"changed-since {args.changed_since}" if args.changed_since else "all"
    print(f"SUMMARY scanned={len(files)} violations={len(violations)} scope={scope}")
    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
