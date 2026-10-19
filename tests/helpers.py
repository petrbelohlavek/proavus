"""Test helpers: a temporary copy of the fictional family repository."""

from __future__ import annotations

import datetime as dt
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import yaml  # noqa: E402

from proavuslib.frontmatter import split  # noqa: E402
from proavuslib.validator import RepoValidator  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "family"
TODAY = dt.date(2026, 10, 20)


class FamilyRepoCase(unittest.TestCase):
    """Each test gets a fresh copy of the fixture it may change."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "family"
        shutil.copytree(FIXTURE, self.repo)

    def tearDown(self):
        self._tmp.cleanup()

    # -- editing helpers
    def path(self, rel: str) -> Path:
        return self.repo / rel

    def find(self, entity_id: str) -> Path:
        hits = [p for p in self.repo.rglob(f"{entity_id}*.md")]
        assert len(hits) == 1, hits
        return hits[0]

    def edit(self, entity_id: str, change):
        """Load a header, let change(data) modify it, write it back."""
        path = self.find(entity_id)
        data, body = split(path.read_text(encoding="utf-8"))
        change(data)
        self.write(path, data, body)

    def write(self, path: Path, data: dict, body: str = "\n"):
        path.parent.mkdir(parents=True, exist_ok=True)
        header = yaml.safe_dump(data, allow_unicode=True, sort_keys=False)
        path.write_text(f"---\n{header}---\n{body}", encoding="utf-8")

    def add(self, rel: str, data: dict, body: str = "\n"):
        self.write(self.repo / rel, data, body)

    # -- running
    def validate(self):
        return RepoValidator(self.repo, ROOT, today=TODAY).run()

    def assertError(self, report, *fragments):
        joined = "\n".join(report.errors)
        for fragment in fragments:
            self.assertIn(fragment, joined, f"expected error containing {fragment!r}; got:\n{joined}")

    def assertWarning(self, report, fragment):
        joined = "\n".join(report.warnings)
        self.assertIn(fragment, joined, f"expected warning containing {fragment!r}; got:\n{joined}")

    def assertClean(self, report):
        self.assertEqual(report.errors, [], "\n".join(report.errors))
