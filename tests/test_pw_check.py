"""Tests for plugins/playwright-tools/scripts/pw-check.py (run: python3 -m unittest discover tests)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/playwright-tools/scripts/pw-check.py"


def write(root: Path, name: str, text: str) -> Path:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def check(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)


def rules(result: subprocess.CompletedProcess) -> set[str]:
    return {line.split()[0] for line in result.stdout.splitlines() if line.startswith("PW")}


class PwCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)

    def test_each_rule_is_reported(self):
        write(self.repo, "tests/bad.spec.ts",
              "import { test, expect } from '@playwright/test';\n"
              "test.only('x', async ({ page }) => {\n"
              "  await page.waitForTimeout(500);\n"
              "  await page.getByRole('button').nth(1).click({ force: true });\n"
              "  await page.locator('.card').click();\n"
              "  expect(await page.getByText('a').isVisible()).toBe(true);\n"
              "  expect(page.getByText('a')).toBeVisible();\n"
              "  expect.poll(() => 1).toBe(1);\n"
              "  await page.pause();\n"
              "});\n")
        result = check(str(self.repo))
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            rules(result),
            {"PW001", "PW002", "PW003", "PW004", "PW005", "PW006", "PW007", "PW008"},
        )

    def test_clean_spec_passes(self):
        write(self.repo, "tests/ok.spec.ts",
              "import { test, expect } from '@playwright/test';\n"
              "test('x', async ({ page }) => {\n"
              "  await page.getByRole('button', { name: 'Save' }).click();\n"
              "  await expect(page.getByText('Saved')).toBeVisible();\n"
              "  await expect.poll(() => 1).toBe(1);\n"
              "  expect(1).toBe(1);\n"
              "});\n")
        result = check(str(self.repo))
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("SUMMARY 0 violation(s) in 1 file(s)", result.stdout)

    def test_ignore_comment_and_commented_code_are_skipped(self):
        write(self.repo, "a.spec.ts",
              "// await page.waitForTimeout(1);\n"
              "await page.locator('table').click(); // pw-check: ignore PW004\n"
              "/*\nawait page.pause();\n*/\n")
        result = check(str(self.repo))
        self.assertEqual(result.returncode, 0, result.stdout)

    def test_non_spec_files_and_node_modules_are_ignored(self):
        write(self.repo, "src/helper.ts", "await page.waitForTimeout(1);\n")
        write(self.repo, "node_modules/x/a.spec.ts", "await page.waitForTimeout(1);\n")
        result = check(str(self.repo))
        self.assertEqual(result.returncode, 3)

    def test_changed_since_limits_to_changed_files(self):
        git = lambda *a: subprocess.run(["git", "-C", str(self.repo), *a], check=True, capture_output=True)
        git("init", "-q")
        git("config", "user.email", "t@t.t")
        git("config", "user.name", "t")
        write(self.repo, "old.spec.ts", "await page.waitForTimeout(1);\n")
        git("add", "-A")
        git("commit", "-qm", "base")
        write(self.repo, "new.spec.ts", "await page.pause();\n")
        result = check(str(self.repo), "--changed-since", "HEAD")
        self.assertEqual(rules(result), {"PW008"})
        self.assertNotIn("old.spec.ts", result.stdout)


if __name__ == "__main__":
    unittest.main()
