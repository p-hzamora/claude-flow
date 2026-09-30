"""Tests for plugins/skills/scripts/brain-file.py (run: python3 -m unittest discover tests)."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/skills/scripts/brain-file.py"

RUN = (
    "<<<NOTE p--r.md\n---\ntype: sdd-run\nproject: p\nrun: r\ndate: 2026-09-30\noutcome: done\n---\n# run\nNOTE>>>"
)
DECISION = (
    "<<<NOTE p--r--D-001.md\n---\ntype: decision\nproject: p\nrun: r\ndate: 2026-09-30\nid: D-001\n---\n# D-001\nNOTE>>>"
)
BAD = "<<<NOTE ../x.md\n---\ntype: sdd-run\nproject: p\nrun: r\ndate: d\noutcome: done\n---\nNOTE>>>"


class BrainFileTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.vault = Path(self._tmp.name)
        (self.vault / "index.md").write_text("# Index\n\n", encoding="utf-8")

    def run_hook(self, message: str, agent_id: str = "a1", vault: Path | None = None):
        payload = json.dumps({"last_assistant_message": message, "agent_id": agent_id})
        return subprocess.run(
            [sys.executable, str(SCRIPT), "--vault", str(vault or self.vault)],
            input=payload, capture_output=True, text=True,
        )

    def test_files_notes_and_indexes(self):
        result = self.run_hook(f"done\n{RUN}\n{DECISION}")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.vault / "projects/p/r.md").is_file())
        self.assertTrue((self.vault / "decisions/p/p--r--D-001.md").is_file())
        self.assertIn("[[projects/p/r|p/r]] — done", (self.vault / "index.md").read_text())

    def test_index_line_is_not_duplicated(self):
        self.run_hook(RUN)
        self.run_hook(RUN, agent_id="a2")
        self.assertEqual((self.vault / "index.md").read_text().count("projects/p/r|"), 1)

    def test_invalid_note_blocks_once_then_is_rejected(self):
        first = self.run_hook(f"{BAD}\n{DECISION}")
        self.assertEqual(first.returncode, 2)
        self.assertIn("file name must match", first.stderr)
        second = self.run_hook(f"{BAD}\n{DECISION}")
        self.assertEqual(second.returncode, 0)
        rejected = sorted(p.name for p in (self.vault / "_rejected").iterdir())
        self.assertEqual(len(rejected), 2)
        self.assertTrue(all(name.endswith((".md", ".reason")) for name in rejected))
        self.assertFalse((self.vault.parent / "x.md").exists())

    def test_message_without_blocks_blocks_then_recovers(self):
        self.assertEqual(self.run_hook("just prose").returncode, 2)
        self.assertEqual(self.run_hook(RUN).returncode, 0)
        self.assertFalse(list(self.vault.glob(".retry-*")))

    def test_missing_vault_exits_1(self):
        result = self.run_hook(RUN, vault=self.vault / "nope")
        self.assertEqual(result.returncode, 1)


if __name__ == "__main__":
    unittest.main()
