"""Tests for plugins/python-suite/scripts/ddd-check.py (run: python3 -m unittest discover tests)."""

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "plugins/python-suite/scripts/ddd-check.py"


def write(root: Path, name: str, text: str) -> None:
    path = root / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def check(repo: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(repo), *extra], capture_output=True, text=True
    )


def rules(result: subprocess.CompletedProcess) -> set[str]:
    return {line.split()[0] for line in result.stdout.splitlines() if line.startswith("DDD-")}


class DddCheckTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.repo = Path(self._tmp.name)

    def test_each_rule_is_reported(self):
        bc = "src/bounded_context"
        write(self.repo, f"{bc}/orders/domain/order.py",
              "from sqlalchemy import Column\n"
              "from bounded_context.orders.infrastructure.repo import X\n"
              "from bounded_context.billing.domain.invoice import Invoice\n")
        write(self.repo, f"{bc}/orders/application/handler.py",
              "from ..infrastructure.repo import X\n")
        write(self.repo, f"{bc}/orders/infrastructure/repo.py", "class MailService: ...\n")
        write(self.repo, "src/shared_kernel/application/port.py",
              "from bounded_context.orders.domain.order import Order\n")
        write(self.repo, "src/core/env.py", "from fastapi import FastAPI\n")
        write(self.repo, f"{bc}/billing/domain/broken.py", "def (\n")
        result = check(self.repo)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(
            rules(result),
            {"DDD-DEP-01", "DDD-DEP-02", "DDD-DEP-03", "DDD-CTX-01", "DDD-CTX-02",
             "DDD-CORE-01", "DDD-ADP-01", "DDD-PARSE"},
        )

    def test_clean_project_passes(self):
        bc = "src/bounded_context/billing"
        write(self.repo, f"{bc}/domain/invoice.py", "from pydantic import BaseModel\n")
        write(self.repo, f"{bc}/domain/clean.py",
              "from .invoice import Invoice\nfrom bounded_context.billing.domain import invoice\n")
        write(self.repo, f"{bc}/application/handler.py",
              "from bounded_context.billing.domain.invoice import Invoice\n")
        write(self.repo, f"{bc}/infrastructure/mailer.py", "class MailerAdapter: ...\n")
        result = check(self.repo)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("violations=0", result.stdout)

    def test_no_topology_exits_3(self):
        write(self.repo, "src/app/main.py", "import fastapi\n")
        result = check(self.repo)
        self.assertEqual(result.returncode, 3)
        self.assertIn("NO_TOPOLOGY", result.stdout)

    def test_changed_since_ignores_existing_debt(self):
        bc = "src/bounded_context/billing"
        write(self.repo, f"{bc}/domain/old.py", "import sqlalchemy\n")
        git = ["git", "-C", str(self.repo)]
        subprocess.run([*git, "init", "-q"], check=True)
        subprocess.run([*git, "add", "-A"], check=True)
        subprocess.run([*git, "-c", "user.email=a@b", "-c", "user.name=t", "commit", "-qm", "base"], check=True)
        write(self.repo, f"{bc}/domain/new.py", "import fastapi\n")
        result = check(self.repo, "--changed-since", "HEAD")
        self.assertEqual(result.returncode, 1)
        self.assertIn("new.py", result.stdout)
        self.assertNotIn("old.py", result.stdout)
        self.assertIn("scanned=1", result.stdout)


if __name__ == "__main__":
    unittest.main()
