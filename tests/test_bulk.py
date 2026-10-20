"""Bulk import (proavuslib.bulk, tools/bulk_import.py) with the fictional example in examples/import/."""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from helpers import ROOT, TODAY

import bulk_import
import family_repo
from proavuslib.bulk import Batch, BulkError, batch_from_plan, load_plan, slugify
from proavuslib.frontmatter import split
from proavuslib.validator import RepoValidator

EXAMPLE = ROOT / "examples" / "import"


class Case(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self._tmp.name) / "proavus-ukazka"
        family_repo.init(self.repo, "Fictional family Ukázka", ["ab:Ada Badatelová"], ["cz"])

    def tearDown(self):
        self._tmp.cleanup()

    def cli(self, *args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = bulk_import.main([*args, "--repo", str(self.repo)])
        return code, out.getvalue() + err.getvalue()

    def entity_files(self):
        return sorted(p for p in self.repo.rglob("*.md")
                      if p.parts[len(self.repo.parts)] not in (".proavus", "archive") and p.name not in ("README.md", "AGENTS.md", "CLAUDE.md"))

    def plan_file(self, text: str) -> Path:
        path = Path(self._tmp.name) / "plan.yaml"
        path.write_text(text, encoding="utf-8")
        return path


class Example(Case):
    """The recommended order on the fictional family: pilot, then the rest."""

    def test_dry_run_writes_nothing(self):
        code, out = self.cli(str(EXAMPLE / "01-pilot.yaml"), "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("14 entities, 0 validation errors", out)
        self.assertEqual(self.entity_files(), [])
        self.assertFalse((self.repo / "archive" / "import-keys.yaml").exists())

    def test_pilot_then_rest(self):
        self.assertEqual(self.cli(str(EXAMPLE / "01-pilot.yaml"))[0], 0)
        code, out = self.cli(str(EXAMPLE / "02-rest.yaml"))     # links @jan of the pilot
        self.assertEqual(code, 0, out)
        report = RepoValidator(self.repo, ROOT, today=TODAY).run()
        self.assertEqual(report.errors, [])
        self.assertEqual(report.files, 20)
        keys = bulk_import.read_keys(self.repo / "archive" / "import-keys.yaml")
        self.assertEqual(len(keys), 20)
        assertions = [split(p.read_text(encoding="utf-8"))[0] for p in self.repo.glob("assertions/*.md")]
        jobs = [a for a in assertions if a.get("fact_type") == "occupation"]
        self.assertEqual(jobs[0]["subject"], keys["jan"])

    def test_every_diary_entry_ends_up_in_a_file(self):
        self.cli(str(EXAMPLE / "01-pilot.yaml"))
        self.cli(str(EXAMPLE / "02-rest.yaml"))
        text = "\n".join(p.read_text(encoding="utf-8") for p in self.entity_files())
        for entry in ("diary 1998-04-11: Archiv Vzorkov", "diary 1998-04-12: matrika O", "diary 2003-09-02: teta Marie", "tree 1: Jan Ukázka × Anna"):
            self.assertIn(entry, text)

    def test_links_and_style(self):
        self.cli(str(EXAMPLE / "01-pilot.yaml"))
        keys = bulk_import.read_keys(self.repo / "archive" / "import-keys.yaml")
        record = next(self.repo.glob("records/R-*.md")).read_text(encoding="utf-8")
        self.assertIn(f"source: {keys['src-n9']}\n", record)
        self.assertIn(f"Linked as {keys['jan']} and {keys['vaclav']}", record)   # @key in the body
        self.assertIn("read_by: [ab]\n", record)                                  # the hand-written style
        self.assertIn("participants:\n  - key: p1\n", record)
        self.assertIn('house_number: "7"\n', record)
        sessions = sorted(p.parent.name for p in self.repo.glob("sessions/*/S-*.md"))
        self.assertEqual(sessions, ["1998", "1998"])
        self.assertTrue(any(p.name.endswith("--jan-ukazka.md") for p in self.repo.glob("people/*.md")))

    def test_same_plan_twice_is_refused(self):
        self.cli(str(EXAMPLE / "01-pilot.yaml"))
        code, out = self.cli(str(EXAMPLE / "01-pilot.yaml"))
        self.assertEqual(code, 1)
        self.assertIn("key 'src-n9' is used twice", out)


class Refusals(Case):
    HEAD = "member: ab\nentities:\n"

    def test_unlinked_diary_entry(self):
        plan = self.plan_file("member: ab\ndiary:\n  - ref: d1\n    text: searched the index\nentities:\n"
                              "  - key: s1\n    type: session\n    date: 2001-02-03\n    by: ab\n    result: x\n    next_step: y\n")
        code, out = self.cli(str(plan))
        self.assertEqual(code, 2)
        self.assertIn("DIARY d1: no entity links this entry", out)
        self.assertEqual(self.entity_files(), [])

    def test_unknown_key(self):
        plan = self.plan_file(self.HEAD + "  - key: q1\n    type: question\n    title: t\n    status: open\n    subjects: ['@nobody']\n")
        code, out = self.cli(str(plan))
        self.assertEqual(code, 1)
        self.assertIn("@nobody – no entity with this key", out)

    def test_validation_errors_write_nothing(self):
        plan = self.plan_file(self.HEAD + "  - key: p1\n    type: person\n    names: [{value: X, name_type: birth}]\n    vital_status: deceased\n    colour: red\n")
        code, out = self.cli(str(plan))
        self.assertEqual(code, 1)
        self.assertIn("colour", out)
        self.assertIn("nothing written", out)
        self.assertEqual(self.entity_files(), [])

    def test_not_a_family_repository(self):
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(out):
            code = bulk_import.main([str(EXAMPLE / "01-pilot.yaml"), "--repo", self._tmp.name])
        self.assertEqual(code, 1)


class Api(Case):
    def batch(self):
        return Batch(self.repo, "ab", ROOT, TODAY)

    def test_add_returns_the_new_id(self):
        b = self.batch()
        pid = b.add("eva", "person", {"names": [{"value": "Eva Ukázková", "name_type": "birth"}], "vital_status": "deceased"})
        self.assertTrue(pid.startswith("P-20261020-ab-"))
        self.assertEqual(b.key_map()["eva"], pid)

    def test_body_links_but_not_e_mails(self):
        b = self.batch()
        pid = b.add("eva", "person", {"names": [{"value": "Eva", "name_type": "birth"}], "vital_status": "deceased"},
                    body="Wrote to podatelna@example.org about @eva; @unknown stays.")
        text = b.files()[0][1]
        self.assertIn(f"about {pid};", text)
        self.assertIn("podatelna@example.org", text)
        self.assertIn("@unknown stays", text)

    def test_rules(self):
        b = self.batch()
        with self.assertRaises(BulkError):
            b.add("Eva", "person", {})                     # key must be lowercase
        with self.assertRaises(BulkError):
            b.add("eva", "persona", {})                    # unknown type
        with self.assertRaises(BulkError):
            b.add("eva", "person", {"id": "P-20261020-ab-xyz"})
        b.add("s", "session", {"by": "ab", "result": "x", "next_step": "y"})
        with self.assertRaises(BulkError):
            b.files()                                      # a session needs a date
        with self.assertRaises(BulkError):
            Batch(self.repo, "Ada", ROOT)

    def test_never_overwrites(self):
        b = self.batch()
        b.add("eva", "person", {"names": [{"value": "Eva", "name_type": "birth"}], "vital_status": "deceased"})
        rel, _ = b.files()[0]
        (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / rel).write_text("---\nkeep: me\n---\n", encoding="utf-8")
        with self.assertRaises(BulkError):
            b.write()
        self.assertEqual((self.repo / rel).read_text(encoding="utf-8"), "---\nkeep: me\n---\n")

    def test_keys_of_earlier_batches(self):
        b = Batch(self.repo, "ab", ROOT, TODAY, known_keys={"jan": "P-20261020-ab-aaa"})
        b.add("q", "question", {"title": "t", "status": "open", "subjects": ["@jan"]})
        self.assertIn("subjects: [P-20261020-ab-aaa]", b.files()[0][1])
        with self.assertRaises(BulkError):
            b.add("jan", "person", {})

    def test_slug(self):
        self.assertEqual(slugify("Matěj Pokusný"), "matej-pokusny")
        self.assertEqual(slugify("Ř Š  Ž!"), "r-s-z")

    def test_plan_loader(self):
        plan = load_plan(EXAMPLE / "01-pilot.yaml")
        batch = batch_from_plan(plan, self.repo, ROOT, today=TODAY)
        self.assertEqual(len(batch.items), 14)
        self.assertEqual(batch.missing_diary(), [])
        with self.assertRaises(BulkError):
            load_plan(self.plan_file("member: ab\n"))


if __name__ == "__main__":
    unittest.main()
