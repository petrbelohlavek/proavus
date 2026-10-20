"""build_views.py: the family map views/mapa.html on the fictional family."""

from __future__ import annotations

import re
import subprocess
import sys
import unittest

from helpers import FamilyRepoCase, ROOT, TODAY

import build_views

SRC = "SO-20261020-ab-s01"
NELA = "P-20261020-ab-n01"
LUCIE = "P-20261020-ab-l01"
KAREL = "P-20261020-ab-k01"
JOSEF = "P-20261020-ab-j01"
MATEJ = "P-20261020-ab-m01"
ANNA = "P-20261020-ab-a01"
VACLAV = "P-20261020-ab-w01"


def fact(id_, subject, fact_type, date=None, **extra):
    data = {"id": id_, "type": "assertion", "kind": "fact", "subject": subject, "fact_type": fact_type}
    if date is not None:
        data["date"] = date
    data.update(extra)
    data["citations"] = [{"source": SRC, "detail": "fictional"}]
    data["confidence"] = "probable"
    return data


def parent_child(id_, parent, child, confidence="probable", subtype="biological"):
    return {"id": id_, "type": "relationship", "rel_type": "parent-child", "subtype": subtype,
            "parties": [{"role": "parent", "person": parent}, {"role": "child", "person": child}],
            "confidence": confidence}


def person(id_, name, status="deceased"):
    return {"id": id_, "type": "person", "names": [{"value": name, "name_type": "birth"}], "sex": "male", "vital_status": status}


class MapCase(FamilyRepoCase):
    """Labels in English: the fictional family's region cz would make them Czech (map.lang default)."""

    def setUp(self):
        super().setUp()
        self.set_map("lang: en")

    def set_map(self, *lines):
        text = self.path("repo.yaml").read_text(encoding="utf-8")
        head, _, block = text.partition("map:\n")
        keep = [line for line in block.splitlines() if line.strip() and not any(line.strip().startswith(new.split(":")[0] + ":") for new in lines)]
        self.path("repo.yaml").write_text(head + "map:\n" + "".join(f"{line}\n" for line in keep) + "".join(f"  {new}\n" for new in lines), encoding="utf-8")

    def build(self, root=None, hide_living=False):
        out, self.builder = build_views.build_map(self.repo, root=root, today=TODAY, hide_living=hide_living)
        self.page = out.read_text(encoding="utf-8")
        return self.page

    def tree(self) -> str:
        start = self.page.index('<div id="tree"')
        return self.page[start:self.page.index('<div class="grid">', start)]

    def in_tree(self) -> list[str]:
        return re.findall(r'<button type="button" class="card[^"]*" data-id="([^"]+)"', self.tree())

    def card(self, pid: str) -> str:
        """The detail of a person (dialog template)."""
        start = self.page.index(f'<template id="d-{pid}">')
        return self.page[start:self.page.index("</template>", start)]

    def box(self, heading: str) -> str:
        start = self.page.index(f"<h2>{heading}</h2>")
        return self.page[start:self.page.index("</section>", start)]

    def edge(self, rel_id: str) -> str:
        m = re.search(rf'<path class="([^"]+)" data-rel="{rel_id}"', self.tree())
        self.assertIsNotNone(m, f"no line for {rel_id}")
        return m.group(1)


class Output(MapCase):
    def test_written_to_views(self):
        self.build()
        self.assertTrue((self.repo / "views" / "mapa.html").is_file())
        self.assertIn("check: no errors", self.page)

    def test_self_contained(self):
        """No CDN, no external styles, scripts, fonts or images (ADR 0027)."""
        self.build()
        for bad in ("<script src", "<link", "@import", "url(", "<img", "<iframe"):
            self.assertNotIn(bad, self.page)
        self.assertIn("Content-Security-Policy", self.page)
        self.assertEqual(set(re.findall(r'(\w+)="https?://', self.page)), {"href"})

    def test_cli(self):
        out = subprocess.run([sys.executable, str(ROOT / "tools" / "build_views.py"), str(self.repo)], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertIn("7 persons", out.stdout)

    def test_czech_labels(self):
        self.set_map("lang: cs")
        self.build()
        self.assertIn('<html lang="cs">', self.page)
        self.assertIn("Výchozí osoba", self.page)
        self.assertIn("<b>křest</b>", self.card(JOSEF))
        self.assertIn("nevlastní", self.card(KAREL))
        self.assertIn("str. 41, fol. 21r, zápis 12", self.card(JOSEF))
        self.assertIn("prvotní · přímý · QUAY 3", self.card(JOSEF))
        self.assertIn("(rozpracovaná)", self.card(MATEJ))
        self.assertIn("(otevřený)", self.card(MATEJ))
        self.assertIn("7 osob ve stromu", self.page)
        self.assertIn("1 otevřená otázka", self.page)


class Root(MapCase):
    def test_root_from_repo_yaml(self):
        self.build()
        self.assertEqual(self.in_tree()[0], NELA)

    def test_root_from_command_line(self):
        self.build(root=JOSEF)
        self.assertEqual(self.in_tree()[0], JOSEF)
        self.assertNotIn(NELA, self.in_tree())
        self.assertIn(f'data-id="{NELA}"', self.box("Persons outside the tree"))

    def test_refuses_framework_and_other_folders(self):
        with self.assertRaises(SystemExit) as cm:
            build_views.build_map(ROOT, today=TODAY)
        self.assertIn("is the Proavus framework", str(cm.exception))
        self.assertFalse((ROOT / "views").exists())
        self.path("repo.yaml").unlink()
        with self.assertRaises(SystemExit) as cm:
            self.build()
        self.assertIn("no repo.yaml", str(cm.exception))

    def test_missing_root(self):
        text = self.path("repo.yaml").read_text(encoding="utf-8")
        self.path("repo.yaml").write_text(text.replace(f"map:\n  root: {NELA}\n", ""), encoding="utf-8")
        with self.assertRaises(SystemExit) as cm:
            self.build()
        self.assertIn("map.root", str(cm.exception))
        with self.assertRaises(SystemExit):
            self.build(root="P-20261020-ab-zzz")


class Tree(MapCase):
    def test_ancestors_of_the_root(self):
        self.build()
        self.assertEqual(sorted(self.in_tree()), sorted([NELA, LUCIE, KAREL, JOSEF, MATEJ, ANNA, VACLAV]))

    def test_line_style_follows_confidence(self):
        self.build()
        self.assertIn("c-proved", self.edge("RL-20261020-ab-f01"))
        self.assertIn("c-probable", self.edge("RL-20261020-ab-f02"))
        self.assertIn("c-possible", self.edge("RL-20261020-ab-f03"))
        for style in ("c-proved", "c-probable", "c-possible"):
            self.assertIn(f".link.{style}", self.page)

    def test_generation_columns_and_marriage(self):
        self.build()
        for label in ("Starting person", "Parents", "Grandparents", "Great-grandparents", "2× great-grandparents"):
            self.assertIn(f">{label}</div>", self.tree())
        self.assertIn('data-rel="RL-20261020-ab-m01"', self.tree())
        self.assertIn("⚭ 1877", self.tree())

    def test_card_colour_follows_evidence(self):
        self.build()
        level = {pid: int(d) for d, pid in re.findall(r'class="card src-(\d)[^"]*" data-id="([^"]+)"', self.tree())}
        self.assertEqual(level[MATEJ], 3)    # primary direct burial register
        self.assertEqual(level[KAREL], 2)    # secondary information
        self.assertEqual(level[ANNA], 0)     # nothing yet
        self.assertIn("1 with an open conflict", self.page)
        self.assertIn("1 open question<", self.page)
        self.assertIn("7 persons in the tree", self.page)
        self.assertIn('<span class="warn" title="open conflict">!</span>', self.tree())

    def test_unknown_parent(self):
        self.build()
        self.assertEqual(self.tree().count('class="card ph src-n"'), 1)
        self.assertIn("unknown parent", self.card(ANNA))

    def test_step_parent_shown_but_not_followed(self):
        self.add("people/P-20261020-ab-o01.md", person("P-20261020-ab-o01", "Ondřej Krokovský"))
        self.add("relationships/RL-20261020-ab-f08.md", parent_child("RL-20261020-ab-f08", "P-20261020-ab-o01", VACLAV))
        self.build()
        self.assertIn("n", self.edge("RL-20261020-ab-f06").split())
        self.assertNotIn("P-20261020-ab-o01", self.in_tree())
        self.assertIn("step", self.card(KAREL))

    def test_disproved_relationship_not_drawn(self):
        self.edit("RL-20261020-ab-f03", lambda d: d.update(confidence="disproved"))
        self.build()
        self.assertNotIn(JOSEF, self.in_tree())
        self.assertIn('<div class="disproved">', self.card(KAREL))

    def test_pedigree_collapse_and_cycle(self):
        self.add("relationships/RL-20261020-ab-f09.md", parent_child("RL-20261020-ab-f09", MATEJ, LUCIE, "possible"))
        self.add("relationships/RL-20261020-ab-f10.md", parent_child("RL-20261020-ab-f10", NELA, MATEJ, "possible"))
        self.build()
        self.assertEqual(self.in_tree().count(MATEJ), 2)
        self.assertEqual(self.tree().count("↺"), 2)  # Matěj again, Nela at the top of the cycle


class Cards(MapCase):
    def test_facts_with_confidence_and_source(self):
        self.build()
        card = self.card(MATEJ)
        for text in ("about 1850", "possible", SRC, "QUAY 2", "† 1910", "Matthias Pokusny"):
            self.assertIn(text, card + self.tree())
        josef = self.card(JOSEF)
        self.assertIn("page 41, folio 21r, entry 12", josef)
        self.assertIn('href="https://example.org/archive/vzorkov-7/image/44"', josef)
        self.assertIn('href="../records/R-20261020-ab-r01.md"', josef)
        self.assertIn("Vzorkov", josef)

    def test_relationships_with_confidence(self):
        self.build()
        card = self.card(MATEJ)
        self.assertIn("Anna Vzorná", card)
        self.assertIn("marriage", card)
        self.assertIn("confirmed ab 20 October 2026", card)

    def test_open_conflict_and_question(self):
        self.build()
        card = self.card(MATEJ)
        self.assertIn("X-20261020-ab-x01", card)
        self.assertIn("Q-20261020-ab-q01", card)
        self.assertIn("born about 1853", self.page)

    def test_resolved_conflict_not_listed(self):
        self.edit("X-20261020-ab-x01", lambda d: d.update(status="resolved", resolution="baptism found"))
        self.build()
        self.assertNotIn("X-20261020-ab-x01", self.page)

    def test_data_is_escaped(self):
        self.edit(ANNA, lambda d: d["names"][0].update(value="<script>alert(1)</script>"))
        self.build()
        self.assertNotIn("<script>alert", self.page)
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", self.page)


class NextSteps(MapCase):
    """ADR 0036, 0037: only open human tasks and inquiries not closed."""

    def test_open_tasks_and_inquiries(self):
        self.build()
        box = self.box("Next steps")
        self.assertIn("human task: Order the marriage register Vzorkov 1870–1878", box)
        self.assertNotIn("copying fee", box)
        self.assertIn(">Obecní úřad Vzorkov (fictional)</a> – Domicile right", box)
        self.edit("IN-20261020-ab-i01", lambda d: d.update(status="closed", result="no record of domicile right"))
        self.build()
        self.assertNotIn("Obecní úřad Vzorkov", self.box("Next steps"))


class LivingPersons(MapCase):
    """Rule 9: living persons only with name, sex, birth and relationships."""

    def test_living_adult_shows_birth_only(self):
        self.add("assertions/A-20261020-ab-o01.md", fact("A-20261020-ab-o01", LUCIE, "occupation", value="secret occupation"))
        self.add("assertions/A-20261020-ab-o02.md", fact("A-20261020-ab-o02", LUCIE, "residence", "2001", place_as_written="Secret street"))
        self.build()
        self.assertIn("2 June 1950", self.card(LUCIE))
        self.assertIn("rule 9", self.card(LUCIE))
        for secret in ("secret occupation", "Secret street", "A-20261020-ab-o01"):
            self.assertNotIn(secret, self.page)

    def test_living_minor_without_birth_date(self):
        self.add("assertions/A-20261020-ab-o03.md", fact("A-20261020-ab-o03", NELA, "birth", "2015-05-05"))
        self.build()
        for date in ("2015-05-05", "5 May 2015", "2015"):
            self.assertNotIn(date, self.page)
        self.assertIn("living minor", self.card(NELA))

    def test_presumed_living_by_birth_year(self):
        self.edit(KAREL, lambda d: d.update(vital_status="unknown"))
        self.edit("A-20261020-ab-b03", lambda d: d.update(date="1930"))
        self.add("assertions/A-20261020-ab-o04.md", fact("A-20261020-ab-o04", KAREL, "occupation", value="secret trade"))
        self.build()
        self.assertNotIn("secret trade", self.page)
        self.assertIn("rule 9", self.card(KAREL))

    def test_partnership_date_of_living_hidden(self):
        self.add("people/P-20261020-ab-o05.md", person("P-20261020-ab-o05", "Petr Partnerský", "living"))
        self.add("relationships/RL-20261020-ab-o05.md", {
            "id": "RL-20261020-ab-o05", "type": "relationship", "rel_type": "partnership", "subtype": "marriage",
            "parties": [{"role": "partner", "person": LUCIE}, {"role": "partner", "person": "P-20261020-ab-o05"}],
            "start": "1975-07-07", "confidence": "probable"})
        self.build()
        self.assertIn("Petr Partnerský", self.card(LUCIE))
        for date in ("1975-07-07", "7 July 1975", "1975"):
            self.assertNotIn(date, self.page)

    def test_conflict_and_question_about_living_hidden(self):
        self.add("conflicts/X-20261020-ab-o06.md", {
            "id": "X-20261020-ab-o06", "type": "conflict", "status": "open", "about": [LUCIE],
            "versions": ["secret version"], "decides": "secret decider"})
        self.add("questions/Q-20261020-ab-o07.md", {
            "id": "Q-20261020-ab-o07", "type": "question", "title": "secret question", "status": "open", "subjects": [LUCIE]})
        self.build()
        self.assertIn("X-20261020-ab-o06", self.card(LUCIE))
        self.assertIn("Q-20261020-ab-o07", self.card(LUCIE))
        for secret in ("secret version", "secret decider", "secret question"):
            self.assertNotIn(secret, self.page)

    def test_no_record_identity_for_living(self):
        self.edit("A-20261020-ab-i02", lambda d: d.update(person=LUCIE))
        self.build()
        self.assertNotIn("In records", self.card(LUCIE))


class Dates(unittest.TestCase):
    """1) Dates in the language of the map, EDTF in words."""

    def test_czech(self):
        cases = {"1958-05-13": "13. 5. 1958", "1868~": "kolem 1868", "1904?": "1904?", "../1836-01-26": "před 26. 1. 1836",
                 "1946/1947": "1946/1947", "1900/..": "po 1900", "1935-04": "duben 1935", "193X": "1930–1939",
                 "1904%": "kolem 1904?", 1958: "1958", "1904-03-02/1906": "2. 3. 1904/1906"}
        for value, expected in cases.items():
            self.assertEqual(build_views.human_date(value, "cs"), expected, value)

    def test_english(self):
        cases = {"1958-05-13": "13 May 1958", "1868~": "about 1868", "../1836-01-26": "before 26 January 1836",
                 "1900/..": "after 1900", "1935-04": "April 1935"}
        for value, expected in cases.items():
            self.assertEqual(build_views.human_date(value, "en"), expected, value)

    def test_unknown_text_is_kept(self):
        self.assertEqual(build_views.human_date("spring of the flood", "cs"), "spring of the flood")

    def test_marriage_label(self):
        for value, expected in (("1877?", "1877?"), ("1877~", "~1877"), ("../1836", "<1836"), ("1900/..", ">1900"), ("1877-05-01", "1877")):
            self.assertEqual(build_views.short_year(value), expected, value)


class Language(MapCase):
    """6) map.lang from the region of the repository when it is missing."""

    def test_default_from_region(self):
        text = self.path("repo.yaml").read_text(encoding="utf-8")
        self.path("repo.yaml").write_text(text.replace("  lang: en\n", ""), encoding="utf-8")
        self.build()
        self.assertIn('<html lang="cs">', self.page)
        self.assertIn("kolem 1850", self.card(MATEJ))
        self.assertIn("14. 3. 1878", self.card(JOSEF))

    def test_english_without_known_region(self):
        text = self.path("repo.yaml").read_text(encoding="utf-8").replace("  lang: en\n", "")
        self.path("repo.yaml").write_text(text.replace("regions: [cz]", "regions: []").replace("extensions: [cz]", "extensions: []"), encoding="utf-8")
        self.build()
        self.assertIn('<html lang="en">', self.page)


class BestFact(MapCase):
    """2) Several facts of one type: the strongest on the card, the others in the detail."""

    def test_equally_strong_versions_are_marked(self):
        self.build()
        card = re.search(rf'<button type="button" class="card[^"]*" data-id="{MATEJ}".*?</button>', self.tree()).group(0)
        self.assertIn("* about 1850", card)       # A-…-b02 and A-…-b05 are equally strong, the first one wins
        self.assertIn('class="alt" title="equally strong other version: about 1853 (possible)"', card)
        detail = self.card(MATEJ)
        self.assertIn("≠ equally strong other version: about 1853 (possible)", detail)
        self.assertIn("shown on the card", detail)
        self.assertIn("other version", detail)

    def test_stronger_information_wins(self):
        self.edit("A-20261020-ab-b05", lambda d: d["citations"][0].update(information="primary", evidence="direct"))
        self.build()
        self.assertIn("* about 1853", self.tree())
        self.assertIn('title="another version disagrees: about 1850 (possible)"', self.tree())

    def test_same_version_twice_is_no_disagreement(self):
        self.edit("A-20261020-ab-b05", lambda d: d.update(date="1850~"))
        self.build()
        self.assertNotIn('class="alt"', self.tree())


class Labels(MapCase):
    """3) Names and titles instead of IDs; 4) long texts shortened on the card."""

    def test_conflict_and_question_boxes_without_ids(self):
        self.build()
        for heading in ("Open conflicts", "Open questions"):
            box = self.box(heading)
            self.assertNotRegex(re.sub(r'(href|title|data-id)="[^"]*"', "", box), r"\b(A|X|Q|P)-20261020-ab-")
        conflicts = self.box("Open conflicts")
        self.assertIn(">Conflict</a> (open)", conflicts)
        self.assertIn(">birth about 1850 – Matěj Pokusný</a>", conflicts)
        self.assertIn(">birth about 1853 – Matěj Pokusný</a>", conflicts)
        self.assertIn('title="X-20261020-ab-x01"', conflicts)
        self.assertIn(">Who were the parents of Matěj Pokusný?</a> (in-progress)", self.box("Open questions"))

    def test_record_title_in_citations(self):
        self.build()
        self.assertIn(">baptism 14 March 1878, Vzorkov („Josephus“)</a>", self.card(JOSEF))

    def test_long_occupation_and_place(self):
        long_place = "Vzorkov, farnost Vzorkov, panství Ukázkov, kraj Příkladný"
        self.edit("A-20261020-ab-b01", lambda d: (d.pop("place"), d.update(place_as_written=long_place)))
        self.build()
        occupation = "sedlák na usedlosti čp. 12 ve Vzorkově, později obecní starosta a kostelník"
        self.assertIn(f'<span class="pf" title="{occupation}">{build_views.clip(occupation, build_views.CLIP_OCCUPATION)}</span>', self.tree())
        self.assertTrue(build_views.clip(occupation, build_views.CLIP_OCCUPATION).endswith("…"))
        self.assertIn(occupation, self.card(MATEJ))
        self.assertIn(f'title="{long_place}">{build_views.clip(long_place, build_views.CLIP_PLACE)}</span>', self.tree())
        self.assertIn(long_place, self.card(JOSEF))


class LivingSettings(MapCase):
    """5) map.living_places and --hide-living."""

    def lucie_card(self):
        return re.search(rf'<button type="button" class="card[^"]*" data-id="{LUCIE}".*?</button>', self.tree()).group(0)

    def test_no_birth_place_of_living_by_default(self):
        self.build()
        self.assertNotIn("Vzorkov", self.lucie_card())
        self.assertNotIn("Vzorkov", self.card(LUCIE))   # neither the place nor the parish register's title
        self.assertNotIn("fictional family register", self.card(LUCIE))
        self.assertIn('href="../sources/SO-20261020-ab-s01.md"', self.card(LUCIE))
        self.assertIn("2 June 1950", self.card(LUCIE))

    def test_living_places_on(self):
        self.set_map("lang: en", "living_places: true")
        self.build()
        self.assertIn("Vzorkov", self.lucie_card())
        self.assertIn("Vzorkov", self.card(LUCIE))
        self.assertIn("fictional family register", self.card(LUCIE))   # source and note shown again

    def test_hide_living_for_sharing(self):
        self.set_map("lang: en", "living_places: true")
        family_map = self.repo / "views" / "mapa.html"
        before = family_map.read_bytes() if family_map.exists() else None
        out, _ = build_views.build_map(self.repo, today=TODAY, hide_living=True)
        self.assertEqual(out.name, "mapa-sdileni.html")
        self.page = out.read_text(encoding="utf-8")
        for secret in ("Lucie Pokusná", "Nela Pokusná", "2 June 1950", "1950", "Search the marriage register"):
            self.assertNotIn(secret, self.page)
        self.assertIn("Living person", self.page)
        self.assertIn("living persons hidden", self.page)
        self.assertNotIn("<h2>Next steps</h2>", self.page)
        self.assertIn("Karel Pokusný", self.page)   # the dead stay as they are
        self.assertEqual(family_map.read_bytes() if family_map.exists() else None, before)  # the family's map is not overwritten

    def test_hide_living_cli(self):
        out = subprocess.run([sys.executable, str(ROOT / "tools" / "build_views.py"), str(self.repo), "--hide-living"], capture_output=True, text=True)
        self.assertEqual(out.returncode, 0, out.stdout + out.stderr)
        self.assertTrue((self.repo / "views" / "mapa-sdileni.html").is_file())

    def test_living_places_must_be_true_or_false(self):
        self.set_map("lang: en", "living_places: sometimes")
        report = self.validate()
        self.assertError(report, "repo.yaml")


if __name__ == "__main__":
    unittest.main()
