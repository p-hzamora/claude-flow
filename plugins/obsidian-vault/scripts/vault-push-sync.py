#!/usr/bin/env python3
"""Toggle and PostToolUse hook for updating a repository's notes in the Obsidian vault after git push.

Usage: vault-push-sync.py [hook|on|off|status]     (default: hook)

Stdlib only. One vault ($BRAIN_VAULT, default ~/Documents/brain) holds every repo under
repos/<repo>/; `update_on_push` in repos/<repo>/brain.config.json is the switch.
`on`/`off`/`status` act on the repo containing the current directory.

`hook` reads the PostToolUse JSON on stdin. It is silent unless the repo is enabled.
If Obsidian's MCP port ($OBSIDIAN_MCP_PORT, default 27123) is closed it tells the user
to start Obsidian; otherwise it injects context asking the main thread to delegate to
`vault-writer`. It never fails the tool call: every error exits 0.
"""

import json
import os
import socket
import subprocess
import sys
from pathlib import Path

DEFAULT_VAULT = "~/Documents/brain"
CONFIG = "brain.config.json"


def git(cwd: Path, *args: str) -> str | None:
    result = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def repo_of(cwd: Path) -> tuple[str, Path] | None:
    top = git(cwd, "rev-parse", "--show-toplevel")
    return (Path(top).name, Path(top)) if top else None


def vault_root() -> Path:
    return Path(os.environ.get("BRAIN_VAULT", DEFAULT_VAULT)).expanduser()


def repo_dir(repo: str) -> Path:
    return vault_root() / "repos" / repo


def load_config(folder: Path) -> dict | None:
    try:
        data = json.loads((folder / CONFIG).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return data if isinstance(data, dict) else None


def obsidian_up() -> bool:
    port = int(os.environ.get("OBSIDIAN_MCP_PORT", "27123"))
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=1):
            return True
    except OSError:
        return False


def hook(payload: dict, reachable=obsidian_up) -> dict | None:
    found = repo_of(Path(payload.get("cwd") or "."))
    if not found:
        return None
    repo, top = found
    folder = repo_dir(repo)
    config = load_config(folder)
    if not config or config.get("update_on_push") is not True:
        return None
    if not reachable():
        return {
            "systemMessage": (
                f"Vault update skipped for `{repo}`: Obsidian is not running. Start Obsidian "
                f"with the vault at {vault_root()} open, then ask vault-writer to update it."
            )
        }
    since = config.get("last_pushed_sha") or "none (first update: use the last 20 commits)"
    context = (
        f"git push succeeded and the vault folder for `{repo}` is enabled for updates. Delegate to the "
        f"`vault-writer` agent now with: repo={repo}; repo_path=repos/{repo}; "
        f"branch={git(top, 'rev-parse', '--abbrev-ref', 'HEAD')}; head={git(top, 'rev-parse', 'HEAD')}; "
        f"since={since}. Include a brief of decisions and gotchas from this session that the "
        "commits do not show."
    )
    return {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}


def toggle(action: str) -> int:
    found = repo_of(Path.cwd())
    if not found:
        print("vault-push-sync: not inside a git repository", file=sys.stderr)
        return 1
    repo, _ = found
    folder = repo_dir(repo)
    config = load_config(folder)
    if action == "status":
        state = "not configured" if config is None else ("on" if config.get("update_on_push") is True else "off")
        print(f"{repo}: {state} ({folder})")
        return 0
    if action == "off" and config is None:
        print(f"{repo}: no config at {folder}; nothing to turn off")
        return 0
    config = config or {}
    config.setdefault("repo", repo)
    config.setdefault("last_pushed_sha", None)
    config["update_on_push"] = action == "on"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / CONFIG).write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"{repo}: update on push {action} ({folder})")
    return 0


def main() -> int:
    action = sys.argv[1] if len(sys.argv) > 1 else "hook"
    if action in ("on", "off", "status"):
        return toggle(action)
    if action != "hook":
        print("usage: vault-push-sync.py [hook|on|off|status]", file=sys.stderr)
        return 1
    try:
        output = hook(json.load(sys.stdin))
    except Exception:
        return 0
    if output:
        print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
