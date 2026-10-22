"""Unit tests of the shared library and the name guard."""

from __future__ import annotations

import contextlib
import datetime as dt
import io
import os
import re
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers  # noqa: F401  (puts tools/ on sys.path)
from helpers import ROOT
from proavuslib import edtf, ids, quay
from proavuslib.frontmatter import split

import guard_names


class Edtf(unittest.TestCase):
    def test_valid(self):
        cases = {
            "1935": (1935, 1935), "1935-04": (1935, 1935), "1935-04-12": (1935, 1935),
            "1935?": (1933, 1937), "1935~": (1933, 1937), "1935%": (1933, 1937),
            "19XX": (1900, 1999), "193X": (1930, 1939), "1935-XX": (1935, 1935),
            "1904/1906": (1904, 1906), "../1900": (0, 1900), "1900/..": (1900, 9999),
            1910: (1910, 1910),
        }
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(edtf.parse(value), expected)

    def test_invalid(self):
        for value in ["1935-13", "1935-02-30", "35", "1935/1930", "../..", "19XX-04", "about 1935", "~1935", True]:
            with self.subTest(value=value):
                self.assertFalse(edtf.is_valid(value))

    def test_leap_day(self):
        self.assertTrue(edtf.is_valid("1904-02-29"))
        self.assertFalse(edtf.is_valid("1900-02-29"))

    def test_single_unspecified_digits(self):
        """ADR 0045: 1855-02-1X, 1855-1X, 1855-02-X5 – the widest range, only real dates."""
        cases = {"1855-02-1X": (1855, 1855), "1855-1X": (1855, 1855), "1855-02-X5": (1855, 1855),
                 "1855-02-1X?": (1853, 1857), "1855-02-13/1855-02-1X": (1855, 1855)}
        for value, expected in cases.items():
            with self.subTest(value=value):
                self.assertEqual(edtf.parse(value), expected)
        self.assertEqual(edtf.expand("1855-02-1X"), (1855, [2], list(range(10, 20)), None))
        self.assertEqual(edtf.expand("1855-1X"), (1855, [10, 11, 12], None, None))
        self.assertEqual(edtf.expand("1855-02-X5"), (1855, [2], [5, 15, 25], None))
        self.assertEqual(edtf.expand("1856-02-2X")[2][-1], 29)      # leap year
        self.assertEqual(edtf.expand("1855-02-2X")[2][-1], 28)
        self.assertIsNone(edtf.expand("185X"))

    def test_single_digits_that_fit_no_date(self):
        for value in ["1855-02-3X", "1855-2X", "1855-XX-1X", "185X-02-1X", "1855-0X-32", "1855-1x"]:
            with self.subTest(value=value):
                self.assertFalse(edtf.is_valid(value))


class Ids(unittest.TestCase):
    def test_new_id_format_and_uniqueness(self):
        seen = set()
        for _ in range(200):
            new = ids.new_id("question", "ab", seen, today=dt.date(2026, 10, 20))
            self.assertRegex(new, r"^Q-20261020-ab-[2-9a-hjkmnp-z]{3}$")
            self.assertNotIn(new, seen)
            seen.add(new)

    def test_prefixes_match_schema(self):
        pattern = re.search(r'"pattern": "\^\((.*?)\)-', (ROOT / "schema/common.schema.json").read_text())[1]
        self.assertEqual(set(pattern.split("|")), set(ids.TYPE_BY_PREFIX))

    def test_bad_member(self):
        with self.assertRaises(ValueError):
            ids.new_id("person", "AB")


class Quay(unittest.TestCase):
    def test_values(self):
        self.assertEqual(quay.quay_for_citation("original", "primary", "direct"), 3)
        self.assertEqual(quay.quay_for_citation("original", "secondary", "direct"), 2)
        self.assertEqual(quay.quay_for_citation("original", "primary", "indirect"), 2)
        self.assertEqual(quay.quay_for_citation("authored", "primary", "direct"), 1)
        self.assertEqual(quay.quay_for_citation("original", "undetermined", "direct"), 1)
        self.assertEqual(quay.quay_for_citation(None, None, None), 0)
        self.assertEqual(quay.quay([("authored", "secondary", "indirect"), ("original", "primary", "direct")]), 3)
        self.assertEqual(quay.quay([]), 0)


class FrontMatter(unittest.TestCase):
    def test_yaml_1_1_traps(self):
        data, body = split("---\non: 2026-10-20\nno: yes\nflag: true\n---\nbody\n")
        self.assertEqual(data, {"on": "2026-10-20", "no": "yes", "flag": True})
        self.assertEqual(body, "body\n")

    def test_unclosed(self):
        with self.assertRaises(ValueError):
            split("---\na: 1\n")


class Pins(unittest.TestCase):
    def test_tool_header_matches_pyproject(self):
        """validate.py runs alone from .proavus/: its PEP 723 pins must equal pyproject's."""
        header = re.search(r"dependencies = (\[.*?\])", (ROOT / "tools/validate.py").read_text())[1]
        project = re.search(r"dependencies = (\[.*?\])", (ROOT / "pyproject.toml").read_text(), re.S)[1]
        norm = lambda s: sorted(re.findall(r'"([^"]+)"', s))
        self.assertEqual(norm(header), norm(project))


class HeaderRoundTrip(unittest.TestCase):
    """join() writes headers back the way people write them (used by migrate.py)."""

    def test_fixture_headers_survive_unchanged(self):
        from proavuslib.frontmatter import join, split
        same = 0
        files = [f for f in (ROOT / "tests" / "fixtures" / "family").rglob("*.md") if f.name != "README.md"]
        for f in files:
            text = f.read_text(encoding="utf-8")
            data, body = split(text)
            out = join(data, body)
            self.assertEqual(split(out), (data, body), f)
            same += out == text
        self.assertGreaterEqual(same, len(files) - 5)   # only optional quotes are not kept

    def test_style(self):
        from proavuslib.frontmatter import join
        out = join({"id": "X", "on": "2026-10-20", "read_by": ["ab", "cd"], "house": "12", "items": [{"path": "a.jpg"}],
                    "note": "two words, a comma", "plan": ["a whole sentence here"]}, "\n")
        self.assertIn("on: 2026-10-20\n", out)
        self.assertIn("read_by: [ab, cd]\n", out)
        self.assertIn('house: "12"\n', out)
        self.assertIn("items:\n  - path: a.jpg\n", out)
        self.assertIn("plan:\n  - a whole sentence here\n", out)


class Guard(unittest.TestCase):
    def test_matching_ignores_case_and_diacritics(self):
        g = guard_names.Guard(["Pokusný"], [])
        self.assertEqual(g.hits("x\nPOKUSNY y"), [(2, 1)])
        self.assertEqual(g.hits("pokusnýho"), [])  # whole words only

    def test_names_inside_identifiers(self):
        g = guard_names.Guard(["Pokusný"], [])
        for text in ("matej_pokusny", "POKUSNY_LINE", "pokusny2", "matejPokusny", "PokusnyFamily", "pokusny-line"):
            self.assertEqual(g.hits(text), [(1, 1)], text)
        for text in ("pokusnyho", "nepokusny", "xpokusny_y"):
            self.assertEqual(g.hits(text), [], text)

    def test_allowed_phrase(self):
        g = guard_names.Guard(["Pokusný"], ["Ada Pokusná-Pokusný"])
        self.assertEqual(g.hits("© Ada Pokusná-Pokusný"), [])
        self.assertEqual(g.hits("Matěj Pokusný"), [(1, 1)])

    def run_with_list(self, content: str | None) -> tuple[int, str]:
        with tempfile.TemporaryDirectory() as tmp:
            list_path = Path(tmp) / ".guard-names"
            if content is not None:
                list_path.write_text(content, encoding="utf-8")
            err = io.StringIO()
            with mock.patch.dict(os.environ, {"PROAVUS_GUARD_NAMES": str(list_path)}), \
                    contextlib.redirect_stderr(err):
                code = guard_names.main(["--all"])
        return code, err.getvalue()

    def test_missing_list_blocks(self):
        code, err = self.run_with_list(None)
        self.assertEqual(code, 2)
        self.assertIn("Commit blocked.", err)

    def test_empty_list_blocks(self):
        # A fictional list with comments only: it guards nothing, so it blocks.
        for content in ("", "\n  \n", "# Pokusný\n# fictional list\n"):
            with self.subTest(content=content):
                code, err = self.run_with_list(content)
                self.assertEqual(code, 2)
                self.assertIn("no entries", err)
                self.assertIn("Commit blocked.", err)
                self.assertNotIn("Pokusný", err)  # never prints the list

    def test_repo_is_clean_when_list_present(self):
        list_path = guard_names.guard_list_path(ROOT)
        if not list_path.exists():
            self.skipTest("guard list not available on this machine")
        self.assertEqual(guard_names.main(["--all"]), 0)


if __name__ == "__main__":
    unittest.main()
