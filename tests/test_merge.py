"""Merging duplicate fact assertions (proavuslib.merge, tools/merge_assertions.py, ADR 0063)."""

from __future__ import annotations

import contextlib
import io
import unittest

from helpers import FamilyRepoCase, ROOT  # noqa: F401  (adds tools/ to sys.path)

import merge_assertions  # noqa: E402
from proavuslib import merge  # noqa: E402
from proavuslib.frontmatter import split  # noqa: E402

MATEJ = "P-20261020-ab-m01"
SRC = "SO-20261020-ab-s01"
B02 = "A-20261020-ab-b02"          # birth 1850~, age at the marriage; named by the conflict X-…-x01
DUP = "A-20261024-ab-b09"          # the same birth from another note
QUESTION = "Q-20261020-ab-q01"


class Merge(FamilyRepoCase):
    def setUp(self):
        super().setUp()
        self.add(f"assertions/{DUP}.md", {
            "id": DUP, "type": "assertion", "kind": "fact", "subject": MATEJ, "fact_type": "birth", "date": "1850~",
            "citations": [{"source": SRC, "detail": "age in the conscription, estimate", "information": "secondary", "evidence": "indirect"}],
            "confidence": "possible", "tags": ["conscription"]}, "\nFrom the house list.\n")
        self.edit(QUESTION, lambda d: d.update(refs=[DUP]))
        path = self.find(QUESTION)
        path.write_text(path.read_text(encoding="utf-8") + f"\nSee {DUP}.\n", encoding="utf-8")

    def plan(self, ids=(B02, DUP), **kw):
        return merge.plan(self.repo, ROOT, list(ids), **kw)

    def cli(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = merge_assertions.main(list(args))
        return code, out.getvalue()

    def test_validator_suggests_the_merge(self):
        self.assertWarning(self.validate(), f"join their citations into one assertion: uv run .proavus/tools/merge_assertions.py plan . {B02} {DUP}")

    def test_plan_keeps_the_one_linked_to(self):
        p = self.plan((DUP, B02))
        self.assertTrue(p.ok, p.problems)
        self.assertEqual((p.keep, p.drop), (B02, [DUP]))
        self.assertEqual(len(p.data["citations"]), 2)
        self.assertEqual(p.data["tags"], ["conscription"])
        self.assertIn(f"questions/{QUESTION}.md", p.links)

    def test_apply(self):
        p = self.plan()
        changed = merge.apply(self.repo, ROOT, p)
        self.assertFalse((self.repo / "assertions" / f"{DUP}.md").exists())
        data, body = split(self.find(B02).read_text(encoding="utf-8"))
        self.assertEqual([c.get("detail") for c in data["citations"]], ["age at the marriage, estimate", "age in the conscription, estimate"])
        self.assertIn(f"## Merged from {DUP}", body)
        self.assertIn("From the house list.", body)
        q, qbody = split(self.find(QUESTION).read_text(encoding="utf-8"))
        self.assertEqual(q["refs"], [B02])
        self.assertIn(f"See {B02}.", qbody)
        self.assertIn(f"assertions/{DUP}.md (deleted)", changed)
        report = self.validate()
        self.assertClean(report)
        self.assertNotIn("join their citations", "\n".join(report.warnings))

    def test_lists_do_not_repeat_the_kept_id(self):
        self.edit(QUESTION, lambda d: d.update(refs=[B02, DUP]))
        merge.apply(self.repo, ROOT, self.plan())
        q, _ = split(self.find(QUESTION).read_text(encoding="utf-8"))
        self.assertEqual(q["refs"], [B02])

    def test_other_confidence_stops(self):
        self.edit(DUP, lambda d: d.update(confidence="probable"))
        p = self.plan()
        self.assertFalse(p.ok)
        self.assertIn("the confidences differ", "\n".join(p.problems))
        p = self.plan(confidence="probable")
        self.assertTrue(p.ok, p.problems)
        self.assertEqual(p.data["confidence"], "probable")

    def test_another_place_is_a_conflict(self):
        self.edit(B02, lambda d: d.update(place="PL-20261020-ab-v01"))
        self.edit(DUP, lambda d: d.update(place_as_written="Lhota"))
        self.assertIn("name different places", "\n".join(self.plan().problems))
        report = self.validate()
        self.assertWarning(report, f"{B02} and {DUP}: the same birth on 1850~ in two places")
        self.assertNotIn("join their citations", "\n".join(report.warnings))

    def test_place_id_and_its_name_are_one_place(self):
        self.edit(B02, lambda d: d.update(place="PL-20261020-ab-v01"))
        self.edit(DUP, lambda d: d.update(place_as_written="Vzorkov"))
        p = self.plan()
        self.assertTrue(p.ok, p.problems)
        self.assertEqual((p.data["place"], p.data["place_as_written"]), ("PL-20261020-ab-v01", "Vzorkov"))

    def test_same_citation_evaluated_otherwise_stops(self):
        self.edit(DUP, lambda d: d.update(citations=[{"source": SRC, "detail": "age at the marriage, estimate",
                                                       "information": "primary", "evidence": "indirect"}]))
        self.assertIn("evaluates the citation", "\n".join(self.plan().problems))

    def test_same_citation_twice_is_joined(self):
        self.edit(DUP, lambda d: d.update(citations=[{"source": SRC, "detail": "age at the marriage, estimate",
                                                       "information": "secondary", "evidence": "indirect"}]))
        self.assertEqual(len(self.plan().data["citations"]), 1)

    def test_confirmation_on_the_one_that_goes_stops(self):
        self.edit(DUP, lambda d: d.update(confirmed={"by": "ab", "on": "2026-10-24"}))
        p = self.plan()
        self.assertIn(f"{DUP} carries a confirmation", "\n".join(p.problems))
        self.assertTrue(self.plan(keep=DUP).ok)

    def test_not_the_same_fact(self):
        self.assertIn("not the same fact", "\n".join(self.plan((B02, "A-20261020-ab-b05")).problems))

    def test_identity_links_are_not_merged_here(self):
        self.assertIn("is an identity link", "\n".join(self.plan((B02, "A-20261020-ab-i01")).problems))

    def test_conflict_naming_both_is_noted(self):
        self.edit("X-20261020-ab-x01", lambda d: d["about"].append(DUP))
        self.assertIn("X-20261020-ab-x01 is about", "\n".join(self.plan().notes))

    def test_cli_plan_all_and_apply(self):
        code, out = self.cli("plan", str(self.repo))
        self.assertEqual(code, 0, out)
        self.assertIn(f"keep {B02}, remove {DUP}", out)
        self.assertTrue((self.repo / "assertions" / f"{DUP}.md").exists())     # plan writes nothing
        code, out = self.cli("apply", str(self.repo), B02, DUP)
        self.assertEqual(code, 0, out)
        self.assertIn("validate: 0 errors", out)
        self.assertFalse((self.repo / "assertions" / f"{DUP}.md").exists())

    def test_cli_apply_with_problems_writes_nothing(self):
        self.edit(DUP, lambda d: d.update(confidence="probable"))
        code, out = self.cli("apply", str(self.repo), B02, DUP)
        self.assertEqual(code, 1)
        self.assertIn("apply: nothing written", out)
        self.assertTrue((self.repo / "assertions" / f"{DUP}.md").exists())


if __name__ == "__main__":
    unittest.main()
