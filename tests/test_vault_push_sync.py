"""Tests for plugins/obsidian-vault/scripts/vault-push-sync.py (run: python3 -m unittest discover tests)."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/obsidian-vault/scripts/vault-push-sync.py"
spec = importlib.util.spec_from_file_location("vault_push_sync", SCRIPT)
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)


class VaultPushSyncTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        tmp = Path(self._tmp.name)
        self.repo = tmp / "myrepo"
        self.repo.mkdir()
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(
            ["git", "-C", str(self.repo), "-c", "user.name=t", "-c", "user.email=t@example.com",
             "commit", "-q", "--allow-empty", "-m", "init"],
            check=True,
        )
        self.root = tmp / "brain"
        self.env = {**os.environ, "BRAIN_VAULT": str(self.root)}
        os.environ["BRAIN_VAULT"] = str(self.root)
        self.addCleanup(os.environ.pop, "BRAIN_VAULT", None)
        self.vault = self.root / "repos" / "myrepo"

    def cli(self, action: str):
        return subprocess.run(
            [sys.executable, str(SCRIPT), action], cwd=self.repo, env=self.env,
            capture_output=True, text=True,
        )

    def enable(self, **extra):
        self.vault.mkdir(parents=True)
        config = {"repo": "myrepo", "update_on_push": True, "last_pushed_sha": None, **extra}
        (self.vault / "brain.config.json").write_text(json.dumps(config), encoding="utf-8")

    def test_hook_silent_without_vault(self):
        self.assertIsNone(sync.hook({"cwd": str(self.repo)}, reachable=lambda: True))

    def test_hook_silent_when_disabled(self):
        self.enable(update_on_push=False)
        self.assertIsNone(sync.hook({"cwd": str(self.repo)}, reachable=lambda: True))

    def test_hook_delegates_when_enabled_and_obsidian_up(self):
        self.enable(last_pushed_sha="abc123")
        out = sync.hook({"cwd": str(self.repo)}, reachable=lambda: True)
        context = out["hookSpecificOutput"]["additionalContext"]
        self.assertIn("vault-writer", context)
        self.assertIn("since=abc123", context)
        self.assertIn("repo_path=repos/myrepo", context)

    def test_hook_tells_user_when_obsidian_down(self):
        self.enable()
        out = sync.hook({"cwd": str(self.repo)}, reachable=lambda: False)
        self.assertIn("Obsidian is not running", out["systemMessage"])
        self.assertNotIn("hookSpecificOutput", out)

    def test_hook_outside_git_repo_is_silent(self):
        self.assertIsNone(sync.hook({"cwd": self._tmp.name}, reachable=lambda: True))

    def test_on_creates_config_then_off_and_status(self):
        self.assertIn("not configured", self.cli("status").stdout)
        self.assertEqual(self.cli("on").returncode, 0)
        config = json.loads((self.vault / "brain.config.json").read_text())
        self.assertEqual(config, {"repo": "myrepo", "last_pushed_sha": None, "update_on_push": True})
        self.assertIn(": on", self.cli("status").stdout)
        self.cli("off")
        self.assertIn(": off", self.cli("status").stdout)

    def test_on_preserves_existing_keys(self):
        self.enable(update_on_push=False, last_pushed_sha="abc123")
        self.cli("on")
        config = json.loads((self.vault / "brain.config.json").read_text())
        self.assertEqual(config["last_pushed_sha"], "abc123")
        self.assertTrue(config["update_on_push"])

    def test_off_without_config_creates_nothing(self):
        self.assertEqual(self.cli("off").returncode, 0)
        self.assertFalse(self.vault.exists())

    def test_hook_cli_swallows_bad_stdin(self):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "hook"], input="not json", env=self.env,
            capture_output=True, text=True,
        )
        self.assertEqual((result.returncode, result.stdout), (0, ""))


if __name__ == "__main__":
    unittest.main()
