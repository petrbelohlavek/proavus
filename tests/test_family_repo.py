"""family_repo.py: creating a family repository, .proavus copy, START-HERE."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import FIXTURE, ROOT, TODAY

import family_repo
from proavuslib.validator import RepoValidator


class Init(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "proavus-test"
        family_repo.init(self.repo, "Rodokmen rodiny Pokusných", ["ab:Ada Badatelová"], ["cz"])

    def tearDown(self):
        self._tmp.cleanup()

    def test_new_repo_is_valid(self):
        report = RepoValidator(self.repo, ROOT, today=TODAY).run()
        self.assertEqual(report.errors, [])
        self.assertEqual(report.files, 0)

    def test_placeholders_filled(self):
        for path in self.repo.rglob("*"):
            if path.is_file() and path.suffix in (".md", ".yaml", ".yml"):
                self.assertNotIn("{{", path.read_text(encoding="utf-8"), path)
        text = (self.repo / "repo.yaml").read_text(encoding="utf-8")
        self.assertIn('extensions: ["cz"]', text)
        self.assertIn('name: "Ada Badatelová"', text)

    def test_generated_files_are_ignored(self):
        ignore = (self.repo / ".gitignore").read_text()
        self.assertIn("START-HERE.md", ignore)
        self.assertIn("views/", ignore)

    def test_framework_blocks_present(self):
        for name in ("CLAUDE.md", "AGENTS.md"):
            text = (self.repo / name).read_text(encoding="utf-8")
            self.assertIn("<!-- proavus:begin -->", text)
            self.assertIn("<!-- proavus:end -->", text)

    def test_pinned_copy_runs_on_its_own(self):
        """The GitHub check uses only .proavus/ (ADR 0014)."""
        copy = self.repo / ".proavus"
        self.assertEqual((copy / "VERSION").read_text().strip(), family_repo.framework_version())
        self.assertFalse((copy / "tools" / "guard_names.py").exists())
        self.assertTrue((copy / "regions" / "cz" / "schema-ext.yaml").is_file())
        target = Path(self._tmp.name) / "fixture"
        shutil.copytree(FIXTURE, target)
        out = subprocess.run([sys.executable, str(copy / "tools" / "validate.py"), str(target)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("16 files, 0 errors", out.stdout)

    def test_refuses_non_empty_folder(self):
        with self.assertRaises(SystemExit):
            family_repo.init(self.repo, "x", ["ab:A"], [])

    def test_member_format(self):
        with self.assertRaises(SystemExit):
            family_repo.init(Path(self._tmp.name) / "other", "x", ["Ada"], [])

    def test_init_into_empty_clone(self):
        """An existing empty repository (only .git) may be used (/proavus:init)."""
        clone = Path(self._tmp.name) / "proavus-clone"
        subprocess.run(["git", "init", "-q", str(clone)], check=True)
        family_repo.init(clone, "x", ["ab:A"], [])
        self.assertTrue((clone / "repo.yaml").is_file())
        self.assertTrue((clone / ".git").is_dir())

    def test_no_remote(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.assertEqual(family_repo.check_private(self.repo), 5)


class StartHere(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "family"
        shutil.copytree(FIXTURE, self.repo)

    def tearDown(self):
        self._tmp.cleanup()

    def test_lists_open_questions_and_next_steps(self):
        summary, code = family_repo.start_here(self.repo, today=TODAY)
        self.assertEqual(code, 0)
        text = (self.repo / "START-HERE.md").read_text(encoding="utf-8")
        self.assertIn("Q-20261020-ab-q01", text)
        self.assertIn("Search the marriage register", text)
        self.assertIn("**Check:** OK", text)
        self.assertIn("1 open questions", summary)

    def test_reports_errors(self):
        (self.repo / "repo.yaml").write_text("schema_version: 0.1.0\nmembers: []\n")
        summary, code = family_repo.start_here(self.repo, today=TODAY)
        self.assertEqual(code, 1)
        self.assertIn("ERRORS", summary)


if __name__ == "__main__":
    unittest.main()
