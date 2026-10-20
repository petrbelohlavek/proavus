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
    def build(self, root=None):
        out, self.builder = build_views.build_map(self.repo, root=root, today=TODAY)
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
        with open(self.repo / "repo.yaml", "a", encoding="utf-8") as f:
            f.write("  lang: cs\n")
        self.build()
        self.assertIn('<html lang="cs">', self.page)
        self.assertIn("Výchozí osoba", self.page)
        self.assertIn("<b>křest</b>", self.card(JOSEF))
        self.assertIn("nevlastní", self.card(KAREL))


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
        for text in ("1850~", "possible", SRC, "QUAY 2", "† 1910", "Matthias Pokusny"):
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
        self.assertIn("confirmed ab 2026-10-20", card)

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


class LivingPersons(MapCase):
    """Rule 9: living persons only with name, sex, birth and relationships."""

    def test_living_adult_shows_birth_only(self):
        self.add("assertions/A-20261020-ab-o01.md", fact("A-20261020-ab-o01", LUCIE, "occupation", value="secret occupation"))
        self.add("assertions/A-20261020-ab-o02.md", fact("A-20261020-ab-o02", LUCIE, "residence", "2001", place_as_written="Secret street"))
        self.build()
        self.assertIn("1950-06-02", self.card(LUCIE))
        self.assertIn("rule 9", self.card(LUCIE))
        for secret in ("secret occupation", "Secret street", "A-20261020-ab-o01"):
            self.assertNotIn(secret, self.page)

    def test_living_minor_without_birth_date(self):
        self.add("assertions/A-20261020-ab-o03.md", fact("A-20261020-ab-o03", NELA, "birth", "2015-05-05"))
        self.build()
        self.assertNotIn("2015-05-05", self.page)
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
        self.assertNotIn("1975-07-07", self.page)

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


if __name__ == "__main__":
    unittest.main()
