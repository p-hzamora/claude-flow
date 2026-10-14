#!/usr/bin/env python3
"""Deterministic anti-pattern checks for Playwright Test specs.

Usage: pw-check.py PATH [PATH ...] [--changed-since REF]

Scans `*.spec.*` and `*.setup.*` files (ts, js, tsx, jsx, mts, cts, mjs, cjs) under each
PATH. Line-based regex checks only; no dependencies beyond the standard library. With
--changed-since, only files that differ from REF (working tree included, plus untracked
files) are reported, so pre-existing debt is not blamed on a run. A line carrying
`pw-check: ignore PW00X` (any comment style) skips that rule for that line.

Output: one `RULE path:line message: <offending line>` per violation, then a SUMMARY line.
Exit: 0 clean, 1 violations, 3 no spec files found.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

SPEC = re.compile(r"\.(spec|setup)\.(?:[mc]?[jt]sx?)$")
EXCLUDED_DIRS = {"node_modules", ".git", "dist", "build", "playwright-report", "test-results"}
WEB_FIRST = (
    "toBeAttached|toBeVisible|toBeHidden|toBeInViewport|toBeEnabled|toBeDisabled|"
    "toBeEditable|toBeEmpty|toBeFocused|toBeChecked|toHaveText|toContainText|toHaveValue|"
    "toHaveValues|toHaveCount|toHaveAttribute|toHaveClass|toContainClass|toHaveId|toHaveCSS|"
    "toHaveJSProperty|toHaveRole|toHaveAccessibleName|toHaveAccessibleDescription|"
    "toHaveScreenshot|toMatchAriaSnapshot|toHaveTitle|toHaveURL|toBeOK"
)
ONE_SHOT = (
    "isVisible|isHidden|isEnabled|isDisabled|isChecked|isEditable|textContent|innerText|"
    "innerHTML|getAttribute|inputValue|count|allTextContents|allInnerTexts"
)

# (rule, pattern, message). Patterns run against a line with string and comment contents kept.
RULES = (
    ("PW001", re.compile(r"\bwaitForTimeout\s*\("), "hard sleep; rely on auto-waiting or a web-first assertion"),
    ("PW002", re.compile(r"\b(?:test|it)(?:\.describe)?(?:\.(?:parallel|serial|configure))?\.only\s*\("), "focused test left in; blocks the rest of the suite"),
    ("PW003", re.compile(r"\.nth\s*\("), "positional locator; filter or use a unique user-facing locator"),
    ("PW004", re.compile(r"\.locator\s*\(\s*(['\"`])"), "string selector; prefer getByRole, getByLabel, getByText, or getByTestId"),
    ("PW005", re.compile(rf"\bexpect\s*\(\s*await\b[^;]*?\.(?:{ONE_SHOT})\s*\("), "one-shot read inside expect; use a web-first assertion that retries"),
    ("PW007", re.compile(r"\bforce\s*:\s*true\b"), "force skips actionability checks and can click an obscured element"),
    ("PW008", re.compile(r"\bpage\.pause\s*\("), "debug pause left in"),
)
# PW006 is separate: an expect statement that starts a line without await/return.
UNAWAITED = re.compile(
    rf"^\s*expect(?:\.soft)?\s*\(.*\)\s*\.(?:not\.)?(?:{WEB_FIRST})\s*\(|^\s*expect(?:\.soft)?\.poll\s*\("
)
IGNORE = re.compile(r"pw-check:\s*ignore\s+((?:PW\d{3}[,\s]*)+)")


def find_specs(paths: list[Path]) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_file() and SPEC.search(path.name):
            found.append(path)
        elif path.is_dir():
            found += [
                p
                for p in path.rglob("*")
                if p.is_file() and SPEC.search(p.name) and not EXCLUDED_DIRS & set(p.parts)
            ]
    return sorted(set(found))


def changed_files(repo: Path, ref: str) -> set[Path]:
    def git(*args: str) -> list[str]:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
        )
        return result.stdout.splitlines()

    names = git("diff", "--name-only", "--relative", "--diff-filter=ACMR", ref)
    names += git("ls-files", "--others", "--exclude-standard")
    return {(repo / name).resolve() for name in names}


def check_file(path: Path) -> list[tuple[str, int, str, str]]:
    violations: list[tuple[str, int, str, str]] = []
    in_block_comment = False
    for number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        stripped = line.strip()
        if in_block_comment:
            in_block_comment = "*/" not in stripped
            continue
        if stripped.startswith("/*"):
            in_block_comment = "*/" not in stripped
            continue
        if stripped.startswith("//"):
            continue
        ignored = set(re.findall(r"PW\d{3}", m.group(1)) if (m := IGNORE.search(line)) else [])
        for rule, pattern, message in RULES:
            if rule not in ignored and pattern.search(line):
                violations.append((rule, number, message, stripped))
        if "PW006" not in ignored and UNAWAITED.search(line):
            violations.append(("PW006", number, "expect without await; the assertion is never awaited", stripped))
    return violations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument("paths", nargs="+", type=Path)
    parser.add_argument("--changed-since", metavar="REF")
    args = parser.parse_args()

    specs = find_specs([p.resolve() for p in args.paths])
    if args.changed_since:
        repo = next((p if p.is_dir() else p.parent for p in (q.resolve() for q in args.paths)), Path.cwd())
        changed = changed_files(repo, args.changed_since)
        specs = [s for s in specs if s in changed]
    if not specs:
        print("SUMMARY no Playwright spec files found")
        return 3

    total = 0
    for spec in specs:
        for rule, number, message, text in check_file(spec):
            print(f"{rule} {spec}:{number} {message}: {text}")
            total += 1
    print(f"SUMMARY {total} violation(s) in {len(specs)} file(s)")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
