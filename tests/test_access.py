"""Access mode of a source and legal time limits of register entries (ADR 0064)."""

from __future__ import annotations

import contextlib
import datetime as dt
import io
import unittest

from helpers import FamilyRepoCase, ROOT, TODAY  # noqa: F401  (adds tools/ to sys.path)

import access as access_tool  # noqa: E402
import family_repo  # noqa: E402
from proavuslib import access  # noqa: E402

SRC = "SO-20261020-ab-s01"
COV = "C-20261020-ab-c02"      # page-through, 1870/1875, negative


class Limits(unittest.TestCase):
    def test_cz_time_limits(self):
        rules = access.rules(ROOT, ["cz"])
        self.assertEqual(access.limit(rules, "baptism").opens(1925), 2025)
        self.assertEqual(access.limit(rules, "marriage").opens(1950), 2025)
        self.assertEqual(access.limit(rules, "burial").opens(1995), 2025)
        self.assertIsNone(access.limit(rules, "census-entry"))
        self.assertIsNone(access.limit(access.rules(ROOT, ["at"]), "death"))   # no rules for at yet

    def test_last_year(self):
        self.assertEqual([access.last_year(x) for x in ("1935", "1930/1960", "193X", "../1900", "1900/..", "1935-04-12")],
                         [1935, 1960, 1939, 1900, None, 1935])


class Sources(FamilyRepoCase):
    def test_known_portal(self):
        self.edit(SRC, lambda d: d.update(portal="acta-publica"))
        self.assertClean(self.validate())

    def test_unknown_portal(self):
        self.edit(SRC, lambda d: d.update(portal="no-such-portal"))
        self.assertWarning(self.validate(), "portal 'no-such-portal' is not in the portal catalogue")

    def test_never_more_than_the_portal(self):
        self.edit(SRC, lambda d: d.update(portal="acta-publica", access={"mode": "automated"}))
        self.assertError(self.validate(), "access mode 'automated', but the portal acta-publica allows only 'link'")

    def test_less_than_the_portal_is_fine(self):
        self.edit(SRC, lambda d: d.update(portal="aron", access={"mode": "on-site", "held_by": "registry-office",
                                                                  "note": "this volume is not digitised"}))
        self.assertClean(self.validate())

    def test_unknown_mode(self):
        self.edit(SRC, lambda d: d.update(access={"mode": "scraping"}))
        self.assertError(self.validate(), "mode")


class Coverage(FamilyRepoCase):
    def test_negative_over_a_closed_range(self):
        self.edit(COV, lambda d: d.update(event="death", ranges=[{"dates": "1990/2000", "pages": "1-29"}]))
        self.assertWarning(self.validate(), "negative over death entries up to 2000: entries younger than 30 years "
                                            "are open to anyone only from 2030")

    def test_negative_over_an_open_range(self):
        self.edit(COV, lambda d: d.update(event="baptism"))
        self.assertNotIn("open to anyone only", "\n".join(self.validate().warnings))

    def test_start_here_lists_inaccessible_searches(self):
        self.edit(COV, lambda d: d.update(event="marriage", result="inaccessible", access_note="book still at the registry office",
                                          ranges=[{"dates": "1940/1960", "pages": "1-29"}]))
        family_repo.start_here(self.repo, today=dt.date(2030, 1, 1))
        text = (self.repo / "START-HERE.md").read_text(encoding="utf-8")
        self.assertIn("- searches not accessible: 1", text)
        self.assertIn("open to anyone from 2035 (75 years for marriage entries) – book still at the registry office", text)
        family_repo.start_here(self.repo, today=dt.date(2036, 1, 1))
        text = (self.repo / "START-HERE.md").read_text(encoding="utf-8")
        self.assertIn("time limit passed in 2035 (75 years for marriage entries): search again", text)


class Cli(FamilyRepoCase):
    def run_tool(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = access_tool.main(list(args), today=TODAY)
        return code, out.getvalue()

    def test_limit(self):
        code, out = self.run_tool("limit", str(self.repo), "--event", "burial", "--year", "2000")
        self.assertEqual(code, 0)
        self.assertIn("burial entry of 2000: not open to anyone until 2030 – 30 years from the entry for death entries", out)
        code, out = self.run_tool("limit", str(self.repo), "--event", "baptism", "--year", "1900")
        self.assertIn("open to anyone now", out)

    def test_source(self):
        self.edit(SRC, lambda d: d.update(portal="acta-publica"))
        code, out = self.run_tool("source", str(self.repo), SRC)
        self.assertEqual(code, 0)
        self.assertIn("portal acta-publica (Acta Publica (Moravský zemský archiv)): link", out)
        self.edit(SRC, lambda d: d.pop("portal"))
        code, out = self.run_tool("source", str(self.repo), SRC)
        self.assertEqual(code, 1)
        self.assertIn("no access mode", out)


if __name__ == "__main__":
    unittest.main()
