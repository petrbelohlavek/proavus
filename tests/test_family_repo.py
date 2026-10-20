"""family_repo.py: creating a family repository, .proavus copy, START-HERE."""

from __future__ import annotations

import json
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
        self.assertIn("30 files, 0 errors", out.stdout)
        out = subprocess.run([sys.executable, str(copy / "tools" / "build_views.py"), str(target)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("Matěj Pokusný", (target / "views" / "mapa.html").read_text(encoding="utf-8"))

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

    def test_init_into_clone_with_claude_settings(self):
        """Opening the empty clone in Claude Code may create .claude/ first."""
        clone = Path(self._tmp.name) / "proavus-clone2"
        subprocess.run(["git", "init", "-q", str(clone)], check=True)
        (clone / ".claude").mkdir()
        (clone / ".claude" / "settings.local.json").write_text('{"permissions": {"allow": []}}\n')
        family_repo.init(clone, "x", ["ab:A"], [])
        self.assertTrue((clone / "repo.yaml").is_file())
        self.assertEqual((clone / ".claude" / "settings.local.json").read_text(), '{"permissions": {"allow": []}}\n')

    def test_init_refuses_other_entries(self):
        for name, make in ((".DS_Store", Path.touch), ("notes", Path.mkdir), (".claude", Path.touch)):
            folder = Path(self._tmp.name) / f"other-{name.strip('.')}"
            folder.mkdir()
            make(folder / name)
            with self.assertRaises(SystemExit) as cm:
                family_repo.init(folder, "x", ["ab:A"], [])
            self.assertIn(name, str(cm.exception))

    def test_install_tools_refuses_framework_and_other_folders(self):
        with self.assertRaises(SystemExit) as cm:
            family_repo.install_tools(ROOT)
        self.assertIn("is the Proavus framework", str(cm.exception))
        self.assertFalse((ROOT / ".proavus").exists())
        other = Path(self._tmp.name) / "other"
        other.mkdir()
        with self.assertRaises(SystemExit) as cm:
            family_repo.install_tools(other)
        self.assertIn("no repo.yaml", str(cm.exception))
        self.assertFalse((other / ".proavus").exists())

    def test_no_remote(self):
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        self.assertEqual(family_repo.check_private(self.repo), 5)


class ProtectPlugin(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "family"
        shutil.copytree(FIXTURE, self.repo)
        self.settings = self.repo / ".claude" / "settings.local.json"

    def tearDown(self):
        self._tmp.cleanup()

    def deny(self):
        return json.loads(self.settings.read_text(encoding="utf-8"))["permissions"]["deny"]

    def test_denies_edits_in_the_plugin_folder(self):
        added = family_repo.protect_plugin(self.repo)
        rule = f"Edit(/{ROOT.resolve().as_posix()}/**)"
        self.assertEqual(added, [rule])
        self.assertTrue(rule.startswith("Edit(//"))  # // = absolute path in Claude Code rules
        self.assertEqual(self.deny(), [rule])

    def test_keeps_other_settings_and_is_idempotent(self):
        self.settings.parent.mkdir()
        self.settings.write_text(json.dumps({"permissions": {"allow": ["Bash(git status)"], "deny": ["Read(./secret)"]}, "x": 1}))
        other = Path(self._tmp.name) / "proavus-checkout"
        other.mkdir()
        family_repo.protect_plugin(self.repo, [other])
        self.assertEqual(family_repo.protect_plugin(self.repo, [other]), [])
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(data["x"], 1)
        self.assertEqual(data["permissions"]["allow"], ["Bash(git status)"])
        self.assertEqual(len(data["permissions"]["deny"]), 3)
        self.assertIn(f"Edit(/{other.resolve().as_posix()}/**)", data["permissions"]["deny"])

    def test_broken_settings_are_not_overwritten(self):
        self.settings.parent.mkdir()
        self.settings.write_text("{broken")
        with self.assertRaises(SystemExit):
            family_repo.protect_plugin(self.repo)
        self.assertEqual(self.settings.read_text(), "{broken")

    def test_only_in_a_family_repository(self):
        own = ROOT / ".claude" / "settings.local.json"
        before = own.read_bytes() if own.exists() else None
        with self.assertRaises(SystemExit):
            family_repo.protect_plugin(ROOT)
        self.assertEqual(own.read_bytes() if own.exists() else None, before)

    def test_settings_are_not_saved_in_git(self):
        ignore = (ROOT / "templates" / "family" / ".gitignore").read_text()
        self.assertIn(".claude/settings.local.json", ignore)


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
