"""family_repo.py: creating a family repository, .proavus copy, START-HERE."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import unittest.mock
from pathlib import Path

from helpers import FIXTURE, ROOT, TODAY

import family_repo
from proavuslib.frontmatter import load_yaml
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
        self.assertIn("37 files, 0 errors", out.stdout)
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

    def test_only_open_human_tasks_and_inquiries(self):
        family_repo.start_here(self.repo, today=TODAY)
        text = (self.repo / "START-HERE.md").read_text(encoding="utf-8")
        self.assertIn("- open human tasks without an open question: 0", text)
        self.assertIn("- open human tasks under their questions above: 1", text)
        self.assertIn("Order the marriage register Vzorkov 1870–1878 in the reading room of Archiv Vzorkov (fictional) (ab)", text)
        self.assertNotIn("Pay the copying fee", text)          # done
        self.assertIn("- inquiries not closed: 1", text)
        self.assertIn("Obecní úřad Vzorkov (fictional): Domicile right (domovské právo) of Matěj Pokusný, 1870–1900 (IN-20261020-ab-i01) – sent 2026-10-20", text)

    def test_names_next_to_ids(self):
        family_repo.start_here(self.repo, today=TODAY)
        text = (self.repo / "START-HERE.md").read_text(encoding="utf-8")
        self.assertIn("### Who were the parents of Matěj Pokusný? (Q-20261020-ab-q01)", text)
        self.assertIn("- about: Matěj Pokusný (P-20261020-ab-m01)", text)
        self.assertIn("baptism 14 March 1878, Vzorkov („Josephus“) (R-20261020-ab-r01)", text)
        self.assertIn("conflict about Matěj Pokusný, birth about 1850 – Matěj Pokusný, birth about 1853 – Matěj Pokusný (X-20261020-ab-x01)", text)
        self.assertIn("S-20261020-ab-s01 – Who were the parents of Matěj Pokusný?:", text)

    def test_summary_per_question(self):
        family_repo.start_here(self.repo, today=TODAY)
        text = (self.repo / "START-HERE.md").read_text(encoding="utf-8")
        section = text[text.index("### Who were"):text.index("## Last sessions")]
        for line in ("- status: in-progress, claimed by ab", "- searched: 3 times (1 found, 2 negative), last 2026-10-20",
                     "- last session 2026-10-20 (ab): next step – Search the marriage register",
                     "- open task: Order the marriage register", "- planned sources: marriage register Vzorkov 1870–1878"):
            self.assertIn(line, section)

    # -- tasks and sessions per question (ADR 0047)
    def write(self, rel: str, header: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"---\n{header}---\n", encoding="utf-8")

    def second_question(self, status: str = "open", extra: str = "") -> None:
        self.write("questions/Q-20261020-ab-q02.md", "id: Q-20261020-ab-q02\ntype: question\n"
                   f"title: When did Josef Pokusný die?\nstatus: {status}\nsubjects: [P-20261020-ab-j01]\n{extra}")

    def session(self, n: str, header: str) -> None:
        self.write(f"sessions/2026/S-20261021-ab-s{n}.md", f"id: S-20261021-ab-s{n}\ntype: session\ndate: 2026-10-21\nby: ab\n"
                   f"result: Fictional result {n}.\n{header}")

    def start(self) -> str:
        summary, code = family_repo.start_here(self.repo, today=TODAY)
        text = (self.repo / "START-HERE.md").read_text(encoding="utf-8")
        self.assertEqual(code, 0, text)
        return text

    @staticmethod
    def section(text: str, qid: str) -> str:
        start = text.index(f"({qid})\n")
        return text[start:text.index("\n### ", start) if "\n### " in text[start:] else text.index("## Last sessions")]

    def test_task_only_under_its_question(self):
        self.second_question()
        self.session("01", "questions: [Q-20261020-ab-q01, Q-20261020-ab-q02]\nnext_step: Wait for the archive.\nhuman_tasks:\n"
                     "  - task: Ask the cemetery office Vzorkov (fictional) for the grave register\n    status: open\n"
                     "    question: Q-20261020-ab-q02\n    conflict: X-20261020-ab-x01\n"
                     "  - task: Photograph the house Vzorkov 12 (fictional)\n    status: open\n")
        text = self.start()
        q1, q2 = self.section(text, "Q-20261020-ab-q01"), self.section(text, "Q-20261020-ab-q02")
        self.assertIn("- open task: Order the marriage register", q1)
        self.assertNotIn("cemetery office", q1)             # the session lists q01 too, but the task is for q02
        self.assertIn("- open task: Ask the cemetery office Vzorkov (fictional) for the grave register – conflict about", q2)
        self.assertNotIn("Order the marriage register", q2)
        waiting = text[text.index("## Waiting for a human"):]
        self.assertIn("- open human tasks without an open question: 1\n  - Photograph the house Vzorkov 12 (fictional) – S-20261021-ab-s01", waiting)
        self.assertIn("- open human tasks under their questions above: 2", waiting)
        for task in ("Order the marriage register", "cemetery office", "Photograph the house"):
            self.assertEqual(text.count(task), 1, task)       # every task once

    def test_task_for_a_closed_question_stays_visible(self):
        self.second_question("answered", "conclusion: Fictional conclusion.\n")
        self.session("01", "questions: [Q-20261020-ab-q02]\nnext_step: Nothing.\nhuman_tasks:\n"
                     "  - task: Return the grave register copy\n    status: open\n    question: Q-20261020-ab-q02\n")
        text = self.start()
        self.assertIn("  - Return the grave register copy – for When did Josef Pokusný die? (Q-20261020-ab-q02), answered – S-20261021-ab-s01", text)
        self.assertIn("WARN sessions/2026/S-20261021-ab-s01.md: open task 'Return the grave register copy' is for question", text)
        self.assertEqual(text[text.index("## Open questions"):].count("Return the grave register copy"), 1)

    def test_last_session_only_where_it_worked_on_the_question(self):
        self.second_question()
        # Lists both questions but holds only the anchor record of q01.
        self.session("01", "questions: [Q-20261020-ab-q01, Q-20261020-ab-q02]\nrecords: [R-20261020-ab-r01]\n"
                     "next_step: Compare the baptism with the marriage.\n")
        text = self.start()
        self.assertIn("- last session 2026-10-21 (ab): next step – Compare the baptism", self.section(text, "Q-20261020-ab-q01"))
        self.assertNotIn("- last session", self.section(text, "Q-20261020-ab-q02"))
        # Lists both questions, nothing of either: no question's last session.
        self.session("02", "questions: [Q-20261020-ab-q01, Q-20261020-ab-q02]\nnext_step: Tidy up the notes.\n")
        text = self.start()
        self.assertNotIn("Tidy up the notes", self.section(text, "Q-20261020-ab-q01") + self.section(text, "Q-20261020-ab-q02"))
        # A task for q02 ties the session to q02; a session with q02 alone is about it.
        self.session("03", "questions: [Q-20261020-ab-q01, Q-20261020-ab-q02]\nnext_step: Wait for the cemetery office.\n"
                     "human_tasks:\n  - task: Ask the cemetery office\n    status: open\n    question: Q-20261020-ab-q02\n")
        text = self.start()
        self.assertIn("next step – Wait for the cemetery office", self.section(text, "Q-20261020-ab-q02"))
        self.assertNotIn("Wait for the cemetery office", self.section(text, "Q-20261020-ab-q01"))
        self.session("04", "questions: [Q-20261020-ab-q02]\nnext_step: Read the death register 1900–1910.\n")
        self.assertIn("next step – Read the death register", self.section(self.start(), "Q-20261020-ab-q02"))

    def test_read_once_records_listed_by_title(self):
        record = self.repo / "records" / "R-20261020-ab-r01.md"
        text = record.read_text(encoding="utf-8")
        record.write_text(text.replace("  status: confirmed\n", "  status: read-once\n"), encoding="utf-8")
        family_repo.start_here(self.repo, today=TODAY)
        self.assertIn("  - baptism 14 March 1878, Vzorkov („Josephus“) (R-20261020-ab-r01)", (self.repo / "START-HERE.md").read_text(encoding="utf-8"))

    def test_plain_text_tasks_only_from_the_latest_session(self):
        session = next(self.repo.glob("sessions/*/S-*.md"))
        text = session.read_text(encoding="utf-8")
        start = text.index("human_tasks:\n")
        session.write_text(text[:start] + "human_tasks:\n  - Call the parish office\n---\n", encoding="utf-8")
        family_repo.start_here(self.repo, today=TODAY)
        self.assertIn("  - Call the parish office – S-20261020-ab-s01", (self.repo / "START-HERE.md").read_text(encoding="utf-8"))
        later = session.parent / "S-20261020-ab-s02.md"
        later.write_text("---\nid: S-20261020-ab-s02\ntype: session\ndate: 2026-10-20\nby: ab\nresult: nothing new\nnext_step: wait\n---\n", encoding="utf-8")
        family_repo.start_here(self.repo, today=TODAY)
        self.assertNotIn("Call the parish office", (self.repo / "START-HERE.md").read_text(encoding="utf-8"))

    def test_upgrade_hint(self):
        family_repo.install_tools(self.repo)
        version = self.repo / ".proavus" / "VERSION"
        version.write_text("0.1.0\n")
        family_repo.start_here(self.repo, today=TODAY)
        self.assertIn("older than the plugin – run `/proavus:upgrade`", (self.repo / "START-HERE.md").read_text(encoding="utf-8"))
        version.write_text("9.0.0\n")
        family_repo.start_here(self.repo, today=TODAY)
        self.assertIn("the plugin is older", (self.repo / "START-HERE.md").read_text(encoding="utf-8"))

    def test_reports_errors(self):
        (self.repo / "repo.yaml").write_text("schema_version: 0.1.0\nmembers: []\n")
        summary, code = family_repo.start_here(self.repo, today=TODAY)
        self.assertEqual(code, 1)
        self.assertIn("ERRORS", summary)


class AddMember(unittest.TestCase):
    """/proavus:setup adds a new family member to repo.yaml (ADR 0048)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "proavus-pokusni"
        family_repo.init(self.repo, "Rodokmen rodiny Pokusných", ["ab:Ada Badatelová"], ["cz"])
        self.yaml = self.repo / "repo.yaml"

    def tearDown(self):
        self._tmp.cleanup()

    def members(self, repo=None):
        return load_yaml(((repo or self.repo) / "repo.yaml").read_text(encoding="utf-8"))["members"]

    def test_adds_member_and_keeps_the_rest(self):
        before = self.yaml.read_text(encoding="utf-8")
        self.assertTrue(family_repo.add_member(self.repo, "bp", "Bedřich Pokusný", "helper"))
        after = self.yaml.read_text(encoding="utf-8")
        self.assertEqual(self.members()[-1], {"abbr": "bp", "name": "Bedřich Pokusný", "role": "helper"})
        self.assertEqual(after.replace('  - abbr: bp\n    name: "Bedřich Pokusný"\n    role: helper\n', ""), before)
        self.assertIn("# map:", after)  # comments stay
        self.assertEqual(RepoValidator(self.repo, ROOT, today=TODAY).run().errors, [])

    def test_already_listed_changes_nothing(self):
        before = self.yaml.read_text(encoding="utf-8")
        self.assertFalse(family_repo.add_member(self.repo, "ab", "Ada Badatelová"))
        self.assertEqual(self.yaml.read_text(encoding="utf-8"), before)

    def test_refuses_taken_abbreviation_name_twice_and_bad_values(self):
        before = self.yaml.read_text(encoding="utf-8")
        for abbr, name, role, fragment in (
            ("ab", "Bedřich Pokusný", "researcher", "already belongs to"),
            ("bp", "ada badatelová", "researcher", "already listed as"),
            ("B1", "Bedřich Pokusný", "researcher", "2–4 lowercase"),
            ("bp", "  ", "researcher", "name is empty"),
            ("bp", "Bedřich Pokusný", "owner", "role must be"),
        ):
            with self.assertRaises(SystemExit) as cm:
                family_repo.add_member(self.repo, abbr, name, role)
            self.assertIn(fragment, str(cm.exception))
        self.assertEqual(self.yaml.read_text(encoding="utf-8"), before)

    def test_fixture_with_map_block(self):
        repo = Path(self._tmp.name) / "fixture"
        shutil.copytree(FIXTURE, repo)
        family_repo.add_member(repo, "cp", "Cecílie Pokusná")
        self.assertEqual([m["abbr"] for m in self.members(repo)], ["ab", "cp"])
        self.assertEqual(RepoValidator(repo, ROOT, today=TODAY).run().errors, [])

    def test_flow_style_members_need_a_hand_edit(self):
        self.yaml.write_text('schema_version: "0.4.0"\nmembers: [{abbr: ab, name: Ada}]\n', encoding="utf-8")
        with self.assertRaises(SystemExit) as cm:
            family_repo.add_member(self.repo, "bp", "Bedřich Pokusný")
        self.assertIn("edit it by hand", str(cm.exception))

    def test_refuses_framework(self):
        with self.assertRaises(SystemExit):
            family_repo.add_member(ROOT, "bp", "Bedřich Pokusný")

    def test_command_line(self):
        self.assertEqual(family_repo.main(["add-member", str(self.repo), "--abbr", "bp", "--name", "Bedřich Pokusný"]), 0)
        self.assertEqual(family_repo.main(["add-member", str(self.repo), "--abbr", "bp", "--name", "Bedřich Pokusný"]), 1)


FAKE_GH = """#!{python}
import os, sys
if os.environ.get("FAKE_GH_ERROR"):
    sys.stderr.write(os.environ["FAKE_GH_ERROR"])
    sys.exit(1)
with open(os.environ["FAKE_GH_ARGS"], "w") as f:
    f.write(" ".join(sys.argv[1:]))
sys.stdout.write(os.environ["FAKE_GH_JSON"])
"""


class Access(unittest.TestCase):
    """Private? Save directly or through a pull request? (ADR 0048) – with a fake gh."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        tmp = Path(self._tmp.name)
        bin_dir = tmp / "bin"
        bin_dir.mkdir()
        gh = bin_dir / "gh"
        gh.write_text(FAKE_GH.format(python=sys.executable), encoding="utf-8")
        gh.chmod(0o755)
        self.args = tmp / "gh-args"
        self.env = {"PATH": f"{bin_dir}{os.pathsep}{os.environ['PATH']}", "FAKE_GH_ARGS": str(self.args)}
        self.repo = tmp / "proavus-pokusni"
        subprocess.run(["git", "init", "-q", str(self.repo)], check=True)
        subprocess.run(["git", "-C", str(self.repo), "remote", "add", "origin", "https://github.com/pokusni/proavus-pokusni.git"], check=True)

    def tearDown(self):
        self._tmp.cleanup()

    def info(self, **kw):
        base = {"nameWithOwner": "pokusni/proavus-pokusni", "visibility": "PRIVATE", "isFork": False, "parent": None}
        return {**base, **kw}

    def test_permissions(self):
        for permission, code in (("ADMIN", 0), ("MAINTAIN", 0), ("WRITE", 2), ("TRIAGE", 6), ("READ", 6), (None, 6)):
            self.assertEqual(family_repo.repo_access(self.info(viewerPermission=permission))[0], code, permission)

    def test_public_or_fork_is_never_written(self):
        self.assertEqual(family_repo.repo_access(self.info(visibility="PUBLIC", viewerPermission="ADMIN"))[0], 3)
        fork = self.info(isFork=True, parent={"name": "proavus"}, viewerPermission="ADMIN")
        self.assertEqual(family_repo.repo_access(fork)[0], 3)

    def run_access(self, target, **env):
        with unittest.mock.patch.dict(os.environ, {**self.env, **env}):
            return family_repo.access(target)

    def test_folder_uses_origin(self):
        code = self.run_access(str(self.repo), FAKE_GH_JSON=json.dumps(self.info(viewerPermission="WRITE")))
        self.assertEqual(code, 2)
        self.assertIn("https://github.com/pokusni/proavus-pokusni.git", self.args.read_text())
        self.assertIn("viewerPermission", self.args.read_text())

    def test_owner_name_before_cloning(self):
        code = self.run_access("pokusni/proavus-pokusni", FAKE_GH_JSON=json.dumps(self.info(viewerPermission="ADMIN")))
        self.assertEqual(code, 0)
        self.assertTrue(self.args.read_text().startswith("repo view pokusni/proavus-pokusni "))

    def test_no_access_yet_and_other_errors(self):
        self.assertEqual(self.run_access("pokusni/proavus-pokusni", FAKE_GH_ERROR="GraphQL: Could not resolve to a Repository with the name"), 7)
        self.assertEqual(self.run_access("pokusni/proavus-pokusni", FAKE_GH_ERROR="error connecting to api.github.com"), 4)

    def test_gh_missing(self):
        with unittest.mock.patch.dict(os.environ, {"PATH": str(Path(self._tmp.name) / "nothing")}):
            self.assertEqual(family_repo.access("pokusni/proavus-pokusni"), 4)

    def test_setup_on_a_fictional_family_repo(self):
        """Step 5–6 of /proavus:setup: clone, check access, add the member, save by access."""
        tmp = Path(self._tmp.name)
        git = ["git", "-c", "user.name=Ada Badatelová", "-c", "user.email=ada@example.invalid"]
        origin = tmp / "origin.git"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
        first = tmp / "maintainer"
        family_repo.init(first, "Rodokmen rodiny Pokusných", ["ab:Ada Badatelová"], ["cz"])
        for cmd in (["init", "-q", "-b", "main"], ["add", "-A"], ["commit", "-q", "-m", "Create"],
                    ["remote", "add", "origin", str(origin)], ["push", "-q", "-u", "origin", "main"]):
            subprocess.run(git + ["-C", str(first)] + cmd, check=True)

        def joins(abbr, name, permission):
            clone = tmp / f"clone-{abbr}"
            subprocess.run(["git", "clone", "-q", str(origin), str(clone)], check=True)
            code = self.run_access(str(clone), FAKE_GH_JSON=json.dumps(self.info(viewerPermission=permission)))
            self.assertTrue(family_repo.add_member(clone, abbr, name))
            self.assertEqual(RepoValidator(clone, ROOT, today=TODAY).run().errors, [])
            run = lambda *cmd: subprocess.run(git + ["-C", str(clone), *cmd], check=True)  # noqa: E731
            if code == 2:
                run("switch", "-q", "-c", f"member-{abbr}")
            run("add", "repo.yaml")
            run("commit", "-q", "-m", f"Add member {abbr} (researcher)")
            run("push", "-q", "-u", "origin", "HEAD")
            return code

        def members_on(branch):
            out = subprocess.run(["git", "-C", str(origin), "show", f"{branch}:repo.yaml"], capture_output=True, text=True, check=True)
            return [m["abbr"] for m in load_yaml(out.stdout)["members"]]

        self.assertEqual(joins("bp", "Bedřich Pokusný", "MAINTAIN"), 0)     # saved straight to main
        self.assertEqual(members_on("main"), ["ab", "bp"])
        self.assertEqual(joins("cp", "Cecílie Pokusná", "WRITE"), 2)        # a branch for the pull request
        self.assertEqual(members_on("main"), ["ab", "bp"])
        self.assertEqual(members_on("member-cp"), ["ab", "bp", "cp"])

    def test_folder_without_origin(self):
        folder = Path(self._tmp.name) / "local"
        subprocess.run(["git", "init", "-q", str(folder)], check=True)
        self.assertEqual(family_repo.access(str(folder)), 4)


if __name__ == "__main__":
    unittest.main()
