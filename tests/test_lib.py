"""Unit tests of the shared library and the name guard."""

from __future__ import annotations

import datetime as dt
import re
import unittest

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

    def test_repo_is_clean_when_list_present(self):
        list_path = guard_names.guard_list_path(ROOT)
        if not list_path.exists():
            self.skipTest("guard list not available on this machine")
        self.assertEqual(guard_names.main(["--all"]), 0)


if __name__ == "__main__":
    unittest.main()
