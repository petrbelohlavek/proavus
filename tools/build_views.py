#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.2", "jsonschema==4.23.0"]
# ///
"""Generate views of a family repository (never saved in git, ADR 0019).

Usage:  uv run .proavus/tools/build_views.py [REPO_DIR] [--root P-…] [--out FILE] [--hide-living]

Writes REPO_DIR/views/mapa.html (ADR 0027–0029): one self-contained HTML file
without any external resources. Header with counts and a legend; the
ancestor tree of the starting person (`map.root` in repo.yaml, or --root) in
generation columns – cards coloured by how well the person is documented,
lines by the confidence of the relationship, marriages on the lines; a
detail dialog for every person (facts with confidence and sources,
relationships, open conflicts and questions); boxes with open conflicts,
open questions, next steps and persons outside the tree.
Living persons show only what rule 9 allows: name, sex, birth and
relationships; living minors without the birth date; their birth place only
with `map.living_places: true`. --hide-living writes a version for sharing
outside the family (views/mapa-sdileni.html): living persons without names
or dates, no next steps.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
FRAMEWORK = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from family_repo import check_family_repo, open_tasks, waiting_inquiries  # noqa: E402
from proavuslib import edtf, ids  # noqa: E402
from proavuslib.frontmatter import load_yaml  # noqa: E402
from proavuslib.quay import quay_for_citation  # noqa: E402
from proavuslib.validator import BIRTH_FACTS, DEATH_FACTS, LIVING_ALLOWED_FACTS, Entity, RepoValidator  # noqa: E402

CONFIDENCE = ["proved", "probable", "possible", "not-proved", "disproved"]
# Parent–child subtypes that continue the line of ancestors; the others
# (step, adoptive, foster, guardian) are shown but not followed further.
OWN_SUBTYPES = (None, "biological", "legitimated", "presumed")
OPEN_CONFLICT = ("open", "unresolved")
OPEN_QUESTION = ("open", "in-progress")
# Card colour = how well the person is documented: best QUAY of their
# visible facts and record identifications (ADR 0022). 0 = no evidence.
DOC_LEVELS = (3, 2, 1, 0)

# Ranking of facts of the same type: information, then evidence, then confidence.
INFORMATION_RANK = {"primary": 0, "secondary": 1, "undetermined": 2}
EVIDENCE_RANK = {"direct": 0, "indirect": 1, "negative": 2}
# Language of the map when map.lang is missing: from the first known region.
REGION_LANG = {"cz": "cs"}
CLIP_OCCUPATION, CLIP_PLACE = 32, 30   # characters on a card; full text in the tooltip and detail

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August",
           "September", "October", "November", "December"],
    "cs": ["leden", "únor", "březen", "duben", "květen", "červen", "červenec", "srpen",
           "září", "říjen", "listopad", "prosinec"],
}
DATE_WORDS = {"en": {"about": "about", "before": "before", "after": "after"},
              "cs": {"about": "kolem", "before": "před", "after": "po"}}
_EDTF = re.compile(r"^([0-9]{4}|[0-9]{3}X|[0-9]{2}XX)(?:-([0-9]{2}|XX)(?:-([0-9]{2}|XX))?)?([?~%])?$")


def human_date(value, lang: str = "en") -> str:
    """EDTF (subset) or ISO date in words: cs 13. 5. 1958, kolem 1868, před 26. 1. 1836, 1946/1947."""
    if value is None:
        return ""
    text = str(value).strip()
    words = DATE_WORDS.get(lang, DATE_WORDS["en"])
    if "/" in text:
        start, _, end = text.partition("/")
        if start in ("", "..") and end not in ("", ".."):
            return f"{words['before']} {human_date(end, lang)}"
        if end in ("", "..") and start not in ("", ".."):
            return f"{words['after']} {human_date(start, lang)}"
        return f"{human_date(start, lang)}/{human_date(end, lang)}"
    m = _EDTF.match(text)
    if not m:
        return text
    year, month, day, qual = m.groups()
    months = MONTHS.get(lang, MONTHS["en"])
    if "X" in year:
        core = f"{year.replace('X', '0')}–{year.replace('X', '9')}"
    elif month and month != "XX" and 1 <= int(month) <= 12:
        if day and day != "XX":
            core = f"{int(day)}. {int(month)}. {year}" if lang == "cs" else f"{int(day)} {months[int(month) - 1]} {year}"
        else:
            core = f"{months[int(month) - 1]} {year}"
    else:
        core = year
    if qual in ("~", "%"):
        core = f"{words['about']} {core}"
    return core + ("?" if qual in ("?", "%") else "")


def short_year(value) -> str:
    """Compact year for the marriage label: ~1877, 1877?, <1836, >1900."""
    text = str(value)
    m = re.search(r"[0-9]{4}|[0-9]{3}X|[0-9]{2}XX", text)
    if not m:
        return ""
    prefix = "<" if text.startswith(("../", "/")) else ">" if text.endswith(("/..", "/")) else "~" if re.search(r"[~%]", text) else ""
    return prefix + m.group(0) + ("?" if re.search(r"[?%]", text) else "")


def clip(text: str, n: int) -> str:
    return text if len(text) <= n else text[: n - 1].rstrip() + "…"


W, H, GX, GY, LEFT, TOP = 210, 160, 64, 16, 14, 46
COLW, SLOT = W + GX, H + GY

LABELS = {
    "en": {
        "map": "family map", "root": "Starting person", "generated": "generated",
        "check_ok": "check: no errors", "check_err": "check: {n} errors – run validate.py",
        "proved": "proved", "probable": "probable", "possible": "possible",
        "not-proved": "not proved", "disproved": "disproved",
        "legend": "Legend", "cards": "Card colour – how well the person is documented",
        "lines": "Line – confidence of the relationship",
        "doc3": "primary direct evidence", "doc2": "secondary or indirect evidence",
        "doc1": "weak evidence (undetermined, authored, negative)", "doc0": "no evidence yet",
        "warn": "open conflict", "nonown": "non-biological", "unknown_parent": "unknown parent",
        "repeat": "already in the tree", "living_short": "living",
        "living": "living – only name, sex, birth and relationships are shown (rule 9)",
        "minor_date": "date not shown (living minor)", "hidden": "details not shown (living person)",
        "chip_tree": ("{n} person in the tree", "{n} persons in the tree"), "chip_doc": ("{n} with primary evidence",),
        "chip_warn": ("{n} with an open conflict",), "chip_q": ("{n} open question", "{n} open questions"),
        "tree": "Tree of ancestors", "tree_sub": "Click a card for the detail with sources.",
        "gen": ["Starting person", "Parents", "Grandparents", "Great-grandparents"],
        "gen_n": "{n}× great-grandparents",
        "birth": "Birth", "death": "Death", "occupation": "Occupation", "other_names": "Other name forms",
        "marriage": "Marriage", "partners": "Partners", "parents": "Parents", "nonown_parents": "Non-biological parents",
        "children": "Children", "facts": "Facts and sources", "identity": "In records",
        "conflicts": "Open conflicts", "questions": "Open questions", "next": "Next steps",
        "outside": "Persons outside the tree", "none": "none", "unknown_value": "unknown",
        "close": "Close", "decides": "What would decide it", "claimed": "claimed by",
        "about": "about", "from": "from", "to": "to", "support": "supported by", "confirmed": "confirmed",
        "human_task": "human task", "bapt": "bapt.", "bur": "bur.",
        "alt_mark": "other version of a fact", "alt_equal": "equally strong other version",
        "alt_conflict": "another version disagrees", "alt_more": "other versions",
        "chosen": "shown on the card", "alternative": "other version",
        "conflict_label": "Conflict", "identity_of": "identity", "session": "session", "inquiry": "inquiry",
        "living_person": "Living person", "hidden_share": "living – hidden in this version for sharing",
        "shared": "version for sharing outside the family – living persons hidden",
        "male": "male", "female": "female", "unknown": "sex unknown",
        "deceased": "deceased", "unknown_status": "vital status unknown", "candidate": "candidate",
    },
    "cs": {
        "map": "mapa rodiny", "root": "Výchozí osoba", "generated": "vygenerováno",
        "check_ok": "kontrola: bez chyb", "check_err": "kontrola: {n} chyb – spusťte validate.py",
        "proved": "prokázáno", "probable": "pravděpodobné", "possible": "možné",
        "not-proved": "neprokázáno", "disproved": "vyvráceno",
        "legend": "Legenda", "cards": "Barva karty – jak je osoba doložená",
        "lines": "Čára – jistota vztahu",
        "doc3": "prvotní přímý doklad", "doc2": "druhotný nebo nepřímý doklad",
        "doc1": "slabý doklad (neurčený, autorský, negativní)", "doc0": "zatím bez dokladu",
        "warn": "otevřený rozpor", "nonown": "nevlastní", "unknown_parent": "neznámý rodič",
        "repeat": "ve stromu už je", "living_short": "žijící",
        "living": "žijící – zobrazeno jen jméno, pohlaví, narození a vztahy (pravidlo 9)",
        "minor_date": "datum neuvedeno (žijící nezletilá osoba)", "hidden": "podrobnosti neuvedeny (žijící osoba)",
        "chip_tree": ("{n} osoba ve stromu", "{n} osoby ve stromu", "{n} osob ve stromu"),
        "chip_doc": ("{n} s prvotním dokladem",), "chip_warn": ("{n} s otevřeným rozporem",),
        "chip_q": ("{n} otevřená otázka", "{n} otevřené otázky", "{n} otevřených otázek"),
        "tree": "Strom předků", "tree_sub": "Klikněte na kartu – otevře se detail se zdroji.",
        "gen": ["Výchozí osoba", "Rodiče", "Prarodiče", "Praprarodiče", "Prapraprarodiče"],
        "gen_n": "{n}. generace předků",
        "birth": "Narození", "death": "Úmrtí", "occupation": "Povolání", "other_names": "Jiné podoby jména",
        "marriage": "Sňatek", "partners": "Partneři", "parents": "Rodiče", "nonown_parents": "Nevlastní rodiče",
        "children": "Děti", "facts": "Údaje a zdroje", "identity": "V záznamech",
        "conflicts": "Otevřené rozpory", "questions": "Otevřené otázky", "next": "Další kroky",
        "outside": "Osoby mimo strom", "none": "žádné", "unknown_value": "neznámé",
        "close": "Zavřít", "decides": "Co rozhodne", "claimed": "zabral/a",
        "about": "týká se", "from": "od", "to": "do", "support": "opírá se o", "confirmed": "potvrdil/a",
        "human_task": "úkol pro člověka", "bapt": "křt.", "bur": "pohř.",
        "alt_mark": "jiná verze údaje", "alt_equal": "stejně silná jiná verze",
        "alt_conflict": "jiná verze se liší", "alt_more": "další verze",
        "chosen": "zobrazeno na kartě", "alternative": "jiná verze",
        "conflict_label": "Rozpor", "identity_of": "identita", "session": "sezení", "inquiry": "dotaz",
        "living_person": "Žijící osoba", "hidden_share": "žijící – v této verzi pro sdílení skryto",
        "shared": "verze pro sdílení mimo rodinu – žijící osoby skryté",
        "male": "muž", "female": "žena", "unknown": "pohlaví neznámé",
        "deceased": "zemřelý/á", "unknown_status": "není známo, zda žije", "candidate": "kandidát",
    },
}


# Schema enum values shown in the map; English shows them as they are.
TERMS = {
    "cs": {
        "open": "otevřený", "unresolved": "nevyřešený", "in-progress": "rozpracovaná",
        "sent": "odesláno", "acknowledged": "potvrzen příjem", "answered": "zodpovězeno",
        "primary": "prvotní", "secondary": "druhotná", "undetermined": "neurčená",
        "direct": "přímý", "indirect": "nepřímý", "negative": "negativní",
        "page": "str.", "folio": "fol.", "entry": "zápis", "image": "snímek",
    },
}


def esc(value) -> str:
    return html.escape(str(value), quote=True)


@dataclass
class Node:
    person: str | None                 # person ID, None = explicitly unknown parent
    rel: Entity | None = None          # relationship to the child (None for the root)
    depth: int = 0
    repeat: bool = False               # already shown elsewhere: not expanded again
    nonown: bool = False               # step / adoptive / foster / guardian: not expanded
    parents: list[Node] = field(default_factory=list)
    row: float = 0.0


class MapBuilder:
    def __init__(self, repo: Path, out: Path, today: dt.date, root: str | None = None, hide_living: bool = False):
        self.repo = repo
        self.out = out
        self.today = today
        self.hide_living = hide_living
        self.v = RepoValidator(repo, FRAMEWORK, today=today)
        self.report = self.v.run()
        config = self.v.config
        settings = config.get("map") if isinstance(config.get("map"), dict) else {}
        self.lang = settings.get("lang") if settings.get("lang") in LABELS else default_lang(config)
        self.living_places = settings.get("living_places") is True
        self.L = LABELS[self.lang]
        self.title = config.get("title") or "Proavus"
        root = root or settings.get("root")
        if not root:
            raise SystemExit("build_views: no starting person – set map.root in repo.yaml or use --root P-…")
        self.root = self.canon(root)
        if self.root not in {e.id for e in self.v.of_type("person")}:
            raise SystemExit(f"build_views: starting person {root} not found in people/")
        self.vocab = _load_vocab()
        self._index()

    # ------------------------------------------------------------- lookups
    def canon(self, id_):
        return self.v.aliases.get(id_, id_) if isinstance(id_, str) else id_

    def get(self, id_) -> Entity | None:
        return self.v.entities.get(self.canon(id_)) if isinstance(id_, str) else None

    def label(self, vocab: str, value) -> str:
        if value is None:
            return ""
        entry = self.vocab.get(vocab, {}).get(value)
        return (entry.get(self.lang) or entry.get("en") or str(value)) if entry else str(value)

    def _index(self) -> None:
        self.people = {e.id: e for e in self.v.of_type("person")}
        self.parent_rels: dict[str, list[Entity]] = {}
        self.child_rels: dict[str, list[Entity]] = {}
        self.partner_rels: dict[str, list[Entity]] = {}
        for rel in sorted(self.v.of_type("relationship"), key=lambda r: r.id):
            parties = [p for p in rel.data.get("parties") or [] if isinstance(p, dict)]
            if rel.data.get("rel_type") == "parent-child":
                for p in parties:
                    if p.get("role") == "child":
                        self.parent_rels.setdefault(self.canon(p.get("person")), []).append(rel)
                    elif p.get("role") == "parent" and p.get("person") != "unknown":
                        self.child_rels.setdefault(self.canon(p.get("person")), []).append(rel)
            else:
                for p in parties:
                    self.partner_rels.setdefault(self.canon(p.get("person")), []).append(rel)
        self.facts: dict[str, list[Entity]] = {}
        self.identities: dict[str, list[Entity]] = {}
        for a in sorted(self.v.of_type("assertion"), key=lambda a: a.id):
            if a.data.get("kind") == "fact":
                self.facts.setdefault(self.canon(a.data.get("subject")), []).append(a)
            elif a.data.get("kind") == "identity":
                self.identities.setdefault(self.canon(a.data.get("person")), []).append(a)
        self.living = {pid for pid, p in self.people.items() if self.v.is_living(p)}
        self.minors = {pid for pid, p in self.people.items() if self.v.is_minor(p)}

    @staticmethod
    def party(rel: Entity, role: str) -> list:
        return [p.get("person") for p in rel.data.get("parties") or [] if isinstance(p, dict) and p.get("role") == role]

    def touches_living(self, ref) -> bool:
        """Is the entity (person, assertion, relationship) about a living person?"""
        ref = self.canon(ref)
        if ref in self.living:
            return True
        e = self.get(ref)
        if e is None:
            return False
        if e.type == "assertion":
            return self.touches_living(e.data.get("subject")) or self.canon(e.data.get("person")) in self.living
        if e.type == "relationship":
            return any(self.canon(p.get("person")) in self.living for p in e.data.get("parties") or [] if isinstance(p, dict))
        return False

    def visible_facts(self, pid: str) -> list[Entity]:
        facts = self.facts.get(pid, [])
        if pid in self.living:
            facts = [a for a in facts if a.data.get("fact_type") in LIVING_ALLOWED_FACTS]
        return sorted(facts, key=lambda a: (_start(a.data.get("date")), a.data.get("fact_type", ""), a.id))

    @staticmethod
    def strength(a: Entity) -> tuple[int, int, int]:
        """(information, evidence, confidence) of the best citation – lower is stronger."""
        best = min(((INFORMATION_RANK.get(c.get("information"), 3), EVIDENCE_RANK.get(c.get("evidence"), 3))
                    for c in a.data.get("citations") or [] if isinstance(c, dict)), default=(3, 3))
        return best + (_rank(a.data.get("confidence")),)

    def best_fact(self, pid: str, types) -> Entity | None:
        found = [a for a in self.visible_facts(pid) if a.data.get("fact_type") in types and a.data.get("confidence") != "disproved"]
        found.sort(key=lambda a: (types.index(a.data["fact_type"]), *self.strength(a), a.id))
        return found[0] if found else None

    def alternatives(self, pid: str, fact: Entity) -> list[Entity]:
        """Other (not disproved) facts of the same type as the chosen one."""
        return [a for a in self.visible_facts(pid) if a is not fact and a.data.get("fact_type") == fact.data.get("fact_type")
                and a.data.get("confidence") != "disproved"]

    def _what(self, a: Entity) -> tuple:
        return (str(a.data.get("date", "")), self.canon(a.data.get("place")) or str(a.data.get("place_as_written", "")).casefold(),
                str(a.data.get("value", "")).casefold())

    def variance(self, pid: str, fact: Entity) -> str | None:
        """'equal' – an equally strong version says something else; 'conflict' – a weaker one does."""
        if pid in self.minors:
            return None
        differing = [a for a in self.alternatives(pid, fact) if self._what(a) != self._what(fact)]
        if not differing:
            return None
        return "equal" if any(self.strength(a) == self.strength(fact) for a in differing) else "conflict"

    def fact_summary(self, pid: str, a: Entity) -> str:
        """Date and place of a fact in words, as allowed for this person (plain text)."""
        date = self.show_date(pid, a)
        parts = [human_date(date, self.lang) if date else "", self.place_shown(pid, a)]
        return ", ".join(x for x in parts if x)

    def show_date(self, pid: str, fact: Entity) -> str | None:
        if pid in self.minors and fact.data.get("fact_type") in BIRTH_FACTS:
            return None
        if self.hidden(pid):
            return None
        date = fact.data.get("date")
        return None if date is None else str(date)

    def hidden(self, pid) -> bool:
        """Living person in a version for sharing outside the family."""
        return self.hide_living and self.canon(pid) in self.living

    def place_shown(self, pid: str, a: Entity) -> str:
        if pid in self.living and (self.hide_living or not self.living_places):
            return ""
        return self.place_text(a)

    def names(self, pid) -> list[dict]:
        if self.hidden(pid):
            return [{"value": self.L["living_person"]}]
        p = self.people.get(self.canon(pid))
        names = [n for n in (p.data.get("names") if p else None) or [] if isinstance(n, dict) and n.get("value")]
        return sorted(names, key=lambda n: not n.get("preferred"))

    def name(self, pid) -> str:
        names = self.names(pid)
        return str(names[0]["value"]) if names else str(pid)

    def place_label(self, place_id, as_written="") -> str:
        place = self.get(place_id)
        if place is not None:
            names = [n for n in place.data.get("names") or [] if isinstance(n, dict)]
            same = [n for n in names if n.get("lang") == self.lang]
            return str((same or names or [{"value": place.id}])[0].get("value"))
        return str(as_written or "")

    def place_text(self, a: Entity) -> str:
        return self.place_label(a.data.get("place"), a.data.get("place_as_written", ""))

    def place_html(self, a: Entity, pid: str | None = None) -> str:
        if pid is not None and not self.place_shown(pid, a):
            return ""
        place = self.get(a.data.get("place"))
        text = esc(self.place_text(a))
        return f'<a href="{esc(self.file_href(place))}">{text}</a>' if place is not None else text

    def occupations(self, pid: str) -> list[str]:
        return [str(a.data["value"]) for a in self.visible_facts(pid)
                if a.data.get("fact_type") == "occupation" and a.data.get("value") is not None and a.data.get("confidence") != "disproved"]

    def doc_level(self, pid: str) -> int:
        """Best QUAY over the person's visible facts and record identifications."""
        if self.hidden(pid):
            return 0
        best = 0
        assertions = self.visible_facts(pid) + ([] if pid in self.living else self.identities.get(pid, []))
        for a in assertions:
            if a.data.get("confidence") == "disproved":
                continue
            for c in a.data.get("citations") or []:
                if isinstance(c, dict):
                    best = max(best, quay_for_citation(self.citation_form(c), c.get("information"), c.get("evidence")))
        return best

    def citation_form(self, c: dict) -> str | None:
        src = None
        if c.get("record"):
            rec = self.get(c["record"])
            src = self.get(rec.data.get("source")) if rec is not None else None
        elif c.get("source"):
            src = self.get(c["source"])
        return src.data.get("form") if src is not None else None

    def warn(self, pid: str) -> bool:
        related = self.related_ids(pid)
        return any(related & {self.canon(r) for r in x.data.get("about") or []} for x in self.open_conflicts())

    def related_ids(self, pid: str) -> set[str]:
        return {pid} | {a.id for a in self.facts.get(pid, [])} | {
            r.id for rels in (self.parent_rels, self.child_rels, self.partner_rels) for r in rels.get(pid, [])}

    def file_href(self, entity: Entity) -> str:
        return Path(os.path.relpath(self.repo / entity.path, self.out.parent)).as_posix()

    def record_title(self, rec: Entity) -> str:
        """A record in words: event, date, place and the principal as written."""
        event = rec.data.get("event") if isinstance(rec.data.get("event"), dict) else {}
        place_text = self.place_label(event.get("place"), event.get("place_as_written", ""))
        principal = next((p.get("name_as_written") for p in rec.data.get("participants") or []
                          if isinstance(p, dict) and p.get("role") == "principal" and p.get("name_as_written")), "")
        head = " ".join(x for x in (self.label("event_types", event.get("type")), human_date(event.get("date"), self.lang)) if x)
        text = ", ".join(x for x in (head, place_text) if x) or rec.id
        return text + (f" („{principal}“)" if principal else "")

    def entity_label(self, e: Entity) -> str:
        """Plain-text name of any entity – what a person reads instead of its ID."""
        d = e.data
        if e.type == "person":
            return self.name(e.id)
        if e.type == "assertion":
            if d.get("kind") == "identity":
                return f"{self.L['identity_of']}: {self.name(d.get('person'))}"
            subject = self.get(d.get("subject"))
            about = self.entity_label(subject) if subject is not None else str(d.get("subject", ""))
            when = human_date(d.get("date"), self.lang) if d.get("date") is not None and not self.touches_living(e.id) else ""
            return " ".join(x for x in (self.label("fact_types", d.get("fact_type")), when) if x) + f" – {about}"
        if e.type == "relationship":
            names = " – ".join(self.L["unknown_parent"] if p.get("person") == "unknown" else self.name(p.get("person"))
                               for p in d.get("parties") or [] if isinstance(p, dict))
            return f"{names} ({self.label('relationship_types', d.get('rel_type'))})"
        if e.type == "record":
            return self.record_title(e)
        if e.type in ("source", "question"):
            return str(d.get("title") or e.id)
        if e.type == "inquiry":
            return str(d.get("addressee") or e.id)
        if e.type == "place":
            names = [n for n in d.get("names") or [] if isinstance(n, dict)]
            return str(names[0].get("value")) if names else e.id
        if e.type == "conflict":
            return self.L["conflict_label"]
        if e.type == "session":
            return f"{self.L['session']} {human_date(d.get('date'), self.lang)}"
        return e.id

    def ref(self, id_) -> str:
        """Button opening a person's detail, or the name of any other entity linked to its file."""
        id_ = self.canon(id_)
        if id_ in self.people:
            return f'<button type="button" class="lnk" data-id="{esc(id_)}">{esc(self.name(id_))}</button>'
        e = self.get(id_)
        if e is None:
            return f"<code>{esc(id_)}</code>"
        return f'<a href="{esc(self.file_href(e))}" title="{esc(id_)}">{esc(self.entity_label(e))}</a>'

    def count(self, key: str, n: int) -> str:
        """Label with the right plural form: en one/other, cs 1 / 2–4 / 5+."""
        forms = self.L[key]
        if self.lang == "cs":
            i = 0 if n == 1 else 1 if 2 <= n <= 4 else 2
        else:
            i = 0 if n == 1 else 1
        return forms[min(i, len(forms) - 1)].format(n=n)

    def term(self, value) -> str:
        """Translate a schema enum value (status, information, evidence, locator part)."""
        return TERMS.get(self.lang, {}).get(value, str(value))

    def id_link(self, e: Entity) -> str:
        return f'<a class="id" href="{esc(self.file_href(e))}">{esc(e.id)}</a>'

    # ----------------------------------------------------------------- tree
    def tree(self) -> Node:
        shown: set[str] = set()

        def build(node: Node) -> Node:
            shown.add(node.person)
            rels = [r for r in self.parent_rels.get(node.person, []) if r.data.get("confidence") != "disproved"]
            rels.sort(key=self._parent_order)
            for rel in rels:
                for parent in self.party(rel, "parent"):
                    nonown = rel.data.get("subtype") not in OWN_SUBTYPES
                    if parent == "unknown":
                        node.parents.append(Node(None, rel, node.depth + 1, nonown=nonown))
                        continue
                    parent = self.canon(parent)
                    if parent not in self.people:
                        continue
                    child = Node(parent, rel, node.depth + 1, repeat=parent in shown, nonown=nonown)
                    node.parents.append(child if child.repeat or nonown else build(child))
                    shown.add(parent)
            return node

        root = build(Node(self.root))
        next_row = [0]

        def place(node: Node) -> None:
            for p in node.parents:
                place(p)
            if node.parents:
                node.row = sum(p.row for p in node.parents) / len(node.parents)
            else:
                node.row = next_row[0]
                next_row[0] += 1

        place(root)
        return root

    def _parent_order(self, rel: Entity):
        parents = self.party(rel, "parent")
        person = self.people.get(self.canon(parents[0])) if parents else None
        sex = person.data.get("sex") if person else None
        return (rel.data.get("subtype") not in OWN_SUBTYPES, {"male": 0, "female": 1}.get(sex, 2), rel.id)

    def gen_label(self, g: int) -> str:
        names = self.L["gen"]
        return names[g] if g < len(names) else self.L["gen_n"].format(n=g if self.lang == "cs" else g - 2)

    def marriage_between(self, a: str | None, b: str | None) -> Entity | None:
        if not a or not b:
            return None
        for rel in self.partner_rels.get(a, []):
            partners = {self.canon(p) for p in self.party(rel, "partner")}
            if b in partners and rel.data.get("confidence") != "disproved":
                return rel
        return None

    def marriage_text(self, rel: Entity) -> tuple[str, str]:
        """(short text for the line, long text) – no dates when a party is living."""
        if self.touches_living(rel.id):
            return "", ""
        fact = next((a for a in self.facts.get(rel.id, []) if a.data.get("fact_type") == "marriage" and a.data.get("confidence") != "disproved"), None)
        date = (fact.data.get("date") if fact else None) or rel.data.get("start")
        place = self.place_text(fact) if fact else ""
        short = short_year(date) if date is not None else ""
        long = ", ".join(x for x in (human_date(date, self.lang) if date is not None else "", place) if x)
        return short, long

    def tree_html(self, root: Node) -> tuple[str, set[str]]:
        nodes: list[Node] = []

        def walk(n: Node):
            nodes.append(n)
            for p in n.parents:
                walk(p)

        walk(root)
        gens = max(n.depth for n in nodes) + 1
        width = LEFT * 2 + (gens - 1) * COLW + W
        height = TOP + max(n.row for n in nodes) * SLOT + H + 24
        svg = [f'<svg width="{width:.0f}" height="{height:.0f}" aria-hidden="true">']
        for n in nodes:
            if not n.parents:
                continue
            x0 = LEFT + n.depth * COLW + W
            xp = LEFT + (n.depth + 1) * COLW
            xm = (x0 + xp) / 2
            y0 = TOP + n.row * SLOT + H / 2
            for p in n.parents:
                y1 = TOP + p.row * SLOT + H / 2
                conf = p.rel.data.get("confidence") if p.rel.data.get("confidence") in CONFIDENCE else "possible"
                cls = f"link c-{conf}" + (" n" if p.nonown else "")
                svg.append(f'<path class="{cls}" data-rel="{esc(p.rel.id)}" d="M{x0:.0f},{y0:.0f} H{xm:.0f} V{y1:.0f} H{xp:.0f}"/>')
            own = [p.person for p in n.parents if not p.nonown]
            rel = self.marriage_between(*own[:2]) if len(own) >= 2 else None
            if rel is not None:
                short, long = self.marriage_text(rel)
                svg.append(f'<g class="mar-g" data-rel="{esc(rel.id)}"><title>{esc(self.L["marriage"])} {esc(long)}</title>'
                           f'<rect class="mar-bg" x="{xm - 28:.0f}" y="{y0 - 29:.0f}" width="56" height="18" rx="9"/>'
                           f'<text class="mar" x="{xm:.0f}" y="{y0 - 20:.0f}">⚭ {esc(short)}</text></g>')
        svg.append("</svg>")
        parts = ["".join(svg)]
        for g in range(gens):
            parts.append(f'<div class="gen" style="left:{LEFT + g * COLW}px;width:{W}px">{esc(self.gen_label(g))}</div>')
        in_tree: set[str] = set()
        for n in nodes:
            if n.person:
                in_tree.add(n.person)
            parts.append(self.card(n))
        return (f'<div id="tree" style="width:{width:.0f}px;height:{height:.0f}px">' + "\n".join(parts) + "</div>"), in_tree

    def card(self, n: Node) -> str:
        style = f"left:{LEFT + n.depth * COLW}px;top:{TOP + n.row * SLOT:.0f}px"
        if n.person is None:
            tag = f'<span class="tag">{esc(self.label("relationship_subtypes", n.rel.data.get("subtype")))}</span>' if n.nonown else ""
            return (f'<div class="card ph src-n" style="{style}"><span class="top">{tag}</span>'
                    f'<span class="nm">? {esc(self.L["unknown_parent"])}</span></div>')
        pid = n.person
        if self.hidden(pid):
            return (f'<button type="button" class="card src-n" data-id="{esc(pid)}" style="{style}"><span class="top"></span>'
                    f'<span class="nm">{esc(self.L["living_person"])}</span><span class="dt"><span class="liv">{esc(self.L["living_short"])}</span></span></button>')
        tags = []
        if n.nonown:
            tags.append(f'<span class="tag n">{esc(self.label("relationship_subtypes", n.rel.data.get("subtype")))}</span>')
        if n.repeat:
            tags.append(f'<span class="tag">↺ {esc(self.L["repeat"])}</span>')
        warn = f'<span class="warn" title="{esc(self.L["warn"])}">!</span>' if self.warn(pid) else ""
        out = [f'<span class="top"><span>{"".join(tags)}</span>{warn}</span>', f'<span class="nm">{esc(self.name(pid))}</span>']
        occ = ", ".join(self.occupations(pid))
        if occ:
            out.append(f'<span class="pf" title="{esc(occ)}">{esc(clip(occ, CLIP_OCCUPATION))}</span>')
        other = [str(x["value"]) for x in self.names(pid)[1:2]]
        if other:
            out.append(f'<span class="or" title="{esc(other[0])}">{esc(other[0])}</span>')
        out.append(f'<span class="dt">{self.dates(pid)}</span>')
        cls = ["card", f"src-{self.doc_level(pid)}"]
        if n.nonown:
            cls.append("nonown")
        return (f'<button type="button" class="{" ".join(cls)}" data-id="{esc(pid)}" style="{style}">'
                + "".join(out) + "</button>")

    def dates(self, pid: str) -> str:
        out = []
        for types, mark in ((BIRTH_FACTS, "birth"), (DEATH_FACTS, "death")):
            fact = self.best_fact(pid, types)
            if fact is None:
                continue
            date = self.show_date(pid, fact)
            if date is None:
                continue
            sign = {"birth": "*", "baptism": self.L["bapt"], "death": "†", "burial": self.L["bur"]}[fact.data["fact_type"]]
            mark = ""
            kind = self.variance(pid, fact)
            if kind:
                others = "; ".join(f"{self.fact_summary(pid, a)} ({self.L.get(a.data.get('confidence'), a.data.get('confidence', ''))})" for a in self.alternatives(pid, fact))
                mark = f' <span class="alt" title="{esc(self.L["alt_" + kind])}: {esc(others)}">≠</span>'
            out.append(f"<span>{esc(sign)} {esc(human_date(date, self.lang))}{mark}</span>")
            place = self.place_shown(pid, fact)
            if place:
                out.append(f'<span class="pl" title="{esc(place)}">{esc(clip(place, CLIP_PLACE))}</span>')
        if pid in self.living:
            out.append(f'<span class="liv">{esc(self.L["living_short"])}</span>')
        return "".join(out)

    # --------------------------------------------------------------- detail
    def conf(self, value) -> str:
        value = value if value in CONFIDENCE else "possible"
        return (f'<span class="conf"><svg width="26" height="8" aria-hidden="true"><line class="link c-{value}" x1="1" y1="4" x2="25" y2="4"/></svg>'
                f"{esc(self.L[value])}</span>")

    def citation(self, c: dict, show_participant: bool, show_source: bool = True) -> str:
        """One citation. For a living person show_participant=False hides the record title and the
        names in it; show_source=False also the source title and note (they name the parish)."""
        parts, url = [], None
        if c.get("record"):
            rec = self.get(c["record"])
            if show_participant or rec is None:
                parts.append(self.ref(c["record"]))
            else:
                parts.append(self.id_link(rec))
            if rec is not None:
                src = self.get(rec.data.get("source"))
                if src is not None and show_source:
                    parts.append(esc(src.data.get("title", "")))
                loc = rec.data.get("locator") or {}
                where = ", ".join(f"{self.term(k)} {loc[k]}" for k in ("page", "folio", "entry", "image") if loc.get(k) is not None)
                if where:
                    parts.append(esc(where))
                url = loc.get("url")
                if show_participant and c.get("participant"):
                    for p in rec.data.get("participants") or []:
                        if isinstance(p, dict) and p.get("key") == c["participant"]:
                            parts.append(f'{esc(p["key"])}: „{esc(p.get("name_as_written", ""))}“ ({esc(self.label("participant_roles", p.get("role")))})')
        elif c.get("source"):
            src = self.get(c["source"])
            if src is not None and show_source:
                parts.append(self.ref(c["source"]))   # the link text is the source title
                url = src.data.get("url")
            elif src is not None:
                parts.append(self.id_link(src))
        else:
            key = next((k for k in ("oral", "coverage") if c.get(k)), None)
            if key:
                parts.append(self.ref(c[key]))
        if c.get("detail") and show_source:
            parts.append(esc(c["detail"]))
        if url and str(url).startswith(("http://", "https://")):
            parts.append(f'<a href="{esc(url)}" rel="noopener noreferrer" target="_blank">↗</a>')
        quality = [self.term(x) for x in (c.get("information"), c.get("evidence")) if x]
        if quality:
            q = quay_for_citation(self.citation_form(c), c.get("information"), c.get("evidence"))
            parts.append(f'<span class="muted">{esc(" · ".join(quality))} · QUAY {q}</span>')
        return " · ".join(p for p in parts if p)

    def detail(self, pid: str) -> str:
        if self.hidden(pid):
            return self.hidden_detail(pid)
        p = self.people[pid]
        L, living = self.L, pid in self.living
        meta = [esc(L.get(p.data.get("sex"), "")) if p.data.get("sex") else ""]
        status = p.data.get("vital_status")
        if living:
            meta.append(esc(L["living"]))
        else:
            meta.append(esc(L["deceased"] if status == "deceased" else L["unknown_status"]))
            meta.append(esc(L[f"doc{self.doc_level(pid)}"]))
        if p.data.get("candidate"):
            meta.append(esc(L["candidate"]))
        meta.append(self.id_link(p))
        out = [f'<template id="d-{esc(pid)}">', f"<h2>{esc(self.name(pid))}</h2>",
               f'<p class="sub">{" · ".join(m for m in meta if m)}</p>', "<dl>"]

        def row(label: str, value: str) -> None:
            out.append(f"<dt>{esc(label)}</dt><dd>{value}</dd>")

        for types, key in ((BIRTH_FACTS, "birth"), (DEATH_FACTS, "death")):
            if key == "death" and living:
                continue
            fact = self.best_fact(pid, types)
            if fact is None:
                row(L[key], f'<span class="muted">{esc(L["unknown_value"])}</span>')
                continue
            date = self.show_date(pid, fact)
            if date is None and fact.data.get("date") is not None:
                text = f'<span class="muted">{esc(L["minor_date"])}</span>'
            else:
                text = esc(human_date(date, self.lang))
            place = self.place_html(fact, pid)
            value = ", ".join(x for x in (text, place) if x) or f'<span class="muted">{esc(L["unknown_value"])}</span>'
            others = self.alternatives(pid, fact) if pid not in self.minors else []
            if others:
                kind = self.variance(pid, fact)
                label = L["alt_" + kind] if kind else L["alt_more"]
                value += (f'<div class="muted">{"≠ " if kind else ""}{esc(label)}: '
                          + "; ".join(f"{esc(self.fact_summary(pid, a))} ({esc(L.get(a.data.get('confidence'), a.data.get('confidence', '')))})" for a in others)
                          + "</div>")
            row(L[key], value)
        occ = self.occupations(pid)
        if occ:
            row(L["occupation"], esc(", ".join(occ)))
        other = self.names(pid)[1:]
        if other:
            row(L["other_names"], ", ".join(
                f'{esc(n["value"])} <span class="muted">({esc(", ".join(x for x in (self.label("name_types", n.get("name_type")), n.get("lang")) if x))})</span>'
                for n in other))
        own = [r for r in self.parent_rels.get(pid, []) if r.data.get("subtype") in OWN_SUBTYPES]
        nonown = [r for r in self.parent_rels.get(pid, []) if r.data.get("subtype") not in OWN_SUBTYPES]
        row(L["parents"], self.rel_list(pid, own, "parent") if own else f'<span class="muted">{esc(L["unknown_value"])}</span>')
        if nonown:
            row(L["nonown_parents"], self.rel_list(pid, nonown, "parent"))
        if self.partner_rels.get(pid):
            row(L["partners"], self.rel_list(pid, self.partner_rels[pid], "partner"))
        if self.child_rels.get(pid):
            row(L["children"], self.rel_list(pid, self.child_rels[pid], "child"))
        out.append("</dl>")

        facts = self.visible_facts(pid)
        chosen = {id(f) for f in (self.best_fact(pid, BIRTH_FACTS), self.best_fact(pid, DEATH_FACTS)) if f is not None}
        if facts:
            out.append(f'<h3>{esc(L["facts"])}</h3><ul class="notes">')
            for a in facts:
                date = self.show_date(pid, a)
                if date is None and a.data.get("date") is not None:
                    date_html = f'<span class="muted">{esc(L["minor_date"])}</span>'
                else:
                    date_html = esc(human_date(date, self.lang))
                what = f"<b>{esc(self.label('fact_types', a.data.get('fact_type')))}</b>"
                if a.data.get("value") is not None:
                    what += f": {esc(a.data['value'])}"
                same = [b for b in facts if b.data.get("fact_type") == a.data.get("fact_type") and b.data.get("confidence") != "disproved"]
                if len(same) > 1 and a.data.get("confidence") != "disproved" and a.data.get("fact_type") in BIRTH_FACTS + DEATH_FACTS:
                    what += f' <span class="tag">{esc(L["chosen"] if id(a) in chosen else L["alternative"])}</span>'
                head = " · ".join(x for x in (what, date_html, self.place_html(a, pid), self.conf(a.data.get("confidence"))) if x)
                show_source = not living or self.living_places
                cites = "".join(f"<li>{self.citation(c, not living, show_source)}</li>" for c in a.data.get("citations") or [] if isinstance(c, dict))
                cls = ' class="disproved"' if a.data.get("confidence") == "disproved" else ""
                out.append(f'<li{cls}>{head} {self.id_link(a)}<ul class="src-list">{cites}</ul></li>')
            out.append("</ul>")
        if not living and self.identities.get(pid):
            out.append(f'<h3>{esc(L["identity"])}</h3><ul class="notes">')
            for a in self.identities[pid]:
                part = a.data.get("participant") or {}
                cite = self.citation({"record": part.get("record"), "participant": part.get("key")}, True)
                out.append(f"<li>{cite} · {self.conf(a.data.get('confidence'))} {self.id_link(a)}</li>")
            out.append("</ul>")
        related = self.related_ids(pid)
        conflicts = [x for x in self.open_conflicts() if related & {self.canon(r) for r in x.data.get("about") or []}]
        questions = [q for q in self.open_questions() if pid in {self.canon(s) for s in q.data.get("subjects") or []}]
        if conflicts:
            out.append(f'<h3>{esc(L["conflicts"])}</h3><ul class="notes">' + "".join(f"<li>{self.conflict(x)}</li>" for x in conflicts) + "</ul>")
        if questions:
            out.append(f'<h3>{esc(L["questions"])}</h3><ul class="notes">' + "".join(f"<li>{self.question(q)}</li>" for q in questions) + "</ul>")
        out.append(f'<button type="button" class="close">{esc(L["close"])}</button></template>')
        return "\n".join(out)

    def hidden_detail(self, pid: str) -> str:
        """A living person in a version for sharing: no name, no facts – only the links of the tree."""
        L = self.L
        out = [f'<template id="d-{esc(pid)}">', f"<h2>{esc(L['living_person'])}</h2>", f'<p class="sub">{esc(L["hidden_share"])}</p>', "<dl>"]
        for label, rels, role in ((L["parents"], self.parent_rels.get(pid, []), "parent"),
                                  (L["partners"], self.partner_rels.get(pid, []), "partner"),
                                  (L["children"], self.child_rels.get(pid, []), "child")):
            if rels:
                out.append(f"<dt>{esc(label)}</dt><dd>{self.rel_list(pid, rels, role)}</dd>")
        out.append(f'</dl><button type="button" class="close">{esc(L["close"])}</button></template>')
        return "\n".join(out)

    def rel_list(self, pid: str, rels: list[Entity], other_role: str) -> str:
        items = []
        for rel in sorted(rels, key=lambda r: (r.data.get("subtype") not in OWN_SUBTYPES, _rank(r.data.get("confidence")), r.id)):
            others = [o for o in self.party(rel, other_role) if self.canon(o) != pid]
            who = ", ".join(esc(self.L["unknown_parent"]) if o == "unknown" else self.ref(o) for o in others) or "–"
            bits = [who]
            subtype = rel.data.get("subtype")
            if subtype:
                tag = "tag n" if rel.data.get("rel_type") == "parent-child" and subtype not in OWN_SUBTYPES else "tag"
                bits.append(f'<span class="{tag}">{esc(self.label("relationship_subtypes", subtype))}</span>')
            bits.append(self.conf(rel.data.get("confidence")))
            if rel.data.get("rel_type") != "parent-child":
                _, long = self.marriage_text(rel)
                if long:
                    bits.append(esc(long))
            elif not self.touches_living(rel.id):
                bits += [f"{self.L[k]} {esc(human_date(rel.data[f], self.lang))}" for k, f in (("from", "start"), ("to", "end")) if rel.data.get(f) is not None]
            support = rel.data.get("assertions") or []
            if support:
                bits.append(f'<span class="muted">{esc(self.L["support"])}</span> ' + ", ".join(self.ref(a) for a in support))
            confirmed = rel.data.get("confirmed")
            if isinstance(confirmed, dict):
                bits.append(f'<span class="muted">{esc(self.L["confirmed"])} {esc(confirmed.get("by", ""))} {esc(human_date(confirmed.get("on"), self.lang))}</span>')
            bits.append(self.id_link(rel))
            cls = ' class="disproved"' if rel.data.get("confidence") == "disproved" else ""
            items.append(f"<div{cls}>{' · '.join(bits)}</div>")
        return "".join(items)

    # -------------------------------------------------- conflicts, questions
    def open_conflicts(self) -> list[Entity]:
        return sorted((c for c in self.v.of_type("conflict") if c.data.get("status") in OPEN_CONFLICT), key=lambda c: c.id)

    def open_questions(self) -> list[Entity]:
        return sorted((q for q in self.v.of_type("question") if q.data.get("status") in OPEN_QUESTION), key=lambda q: q.id)

    def conflict(self, x: Entity) -> str:
        head = f'<a href="{esc(self.file_href(x))}" title="{esc(x.id)}">{esc(self.L["conflict_label"])}</a> ({esc(self.term(x.data.get("status")))})'
        about = x.data.get("about") or []
        if any(self.touches_living(r) for r in about):
            return f'{head} <span class="muted">{esc(self.L["hidden"])}</span>'
        out = f'{head} · {esc(self.L["about"])}: ' + ", ".join(self.ref(r) for r in about)
        versions = x.data.get("versions") or []
        if versions:
            out += "<ol>" + "".join(f"<li>{esc(v)}</li>" for v in versions) + "</ol>"
        if x.data.get("decides"):
            out += ("" if versions else "<br>") + f'{esc(self.L["decides"])}: {esc(x.data["decides"])}'
        return out

    def question(self, q: Entity) -> str:
        status = f'({esc(self.term(q.data.get("status")))})'
        subjects = q.data.get("subjects") or []
        if any(self.touches_living(s) for s in subjects):
            return f'<a href="{esc(self.file_href(q))}" title="{esc(q.id)}">{esc(self.L["questions"])}</a> {status} <span class="muted">{esc(self.L["hidden"])}</span>'
        out = f'<a href="{esc(self.file_href(q))}" title="{esc(q.id)}">{esc(q.data.get("title") or q.id)}</a> {status}'
        if subjects:
            out += f' · {esc(self.L["about"])}: ' + ", ".join(self.ref(s) for s in subjects)
        if q.data.get("claimed_by"):
            out += f' · <span class="muted">{esc(self.L["claimed"])} {esc(q.data["claimed_by"])}</span>'
        return out

    def next_steps(self) -> list[str]:
        """Next steps of the last sessions, then open human tasks and inquiries not closed (ADR 0036, 0037)."""
        sessions = sorted(self.v.of_type("session"), key=lambda s: (str(s.data.get("date", "")), s.id), reverse=True)[:5]
        out = [f'<b>{esc(human_date(s.data.get("date"), self.lang))}</b> ({esc(s.data.get("by", ""))}) {esc(s.data.get("next_step", ""))} {self.id_link(s)}'
               for s in sessions]
        for sid, task, who in open_tasks(self.v.of_type("session")):
            out.append(f'{esc(self.L["human_task"])}: {esc(task)}' + (f" ({esc(who)})" if who else "") + f" {self.id_link(self.get(sid))}")
        for inq in waiting_inquiries(self.v.of_type("inquiry")):
            out.append(f'{esc(self.L["inquiry"])}: {self.ref(inq.id)} – {esc(inq.data.get("subject", ""))} '
                       f'({esc(self.term(inq.data.get("status")))} {esc(human_date(inq.data.get("sent"), self.lang))})')
        return out

    # ------------------------------------------------------------------ page
    def render(self) -> str:
        L = self.L
        tree, in_tree = self.tree_html(self.tree())
        check = L["check_ok"] if self.report.ok else L["check_err"].format(n=len(self.report.errors))
        chips = [self.count("chip_tree", len(in_tree)),
                 self.count("chip_doc", sum(1 for p in in_tree if self.doc_level(p) == 3)),
                 self.count("chip_warn", sum(1 for p in in_tree if self.warn(p))),
                 self.count("chip_q", len(self.open_questions()))]
        legend_cards = "".join(f'<span><i class="sw src-{d}"></i>{esc(L[f"doc{d}"])}</span>' for d in DOC_LEVELS)
        legend_cards += f'<span><span class="warn">!</span>{esc(L["warn"])}</span><span><span class="alt">≠</span>{esc(L["alt_mark"])}</span>'
        legend_lines = "".join(f"<span>{self.conf(c)}</span>" for c in CONFIDENCE[:4])
        legend_lines += f'<span><svg width="26" height="8" aria-hidden="true"><line class="link n" x1="1" y1="4" x2="25" y2="4"/></svg>{esc(L["nonown"])}</span>'
        people = sorted(self.people, key=lambda pid: (self.name(pid).casefold(), pid))
        details = "\n".join(self.detail(pid) for pid in people)
        none = f"<li class='muted'>{esc(L['none'])}</li>"
        boxes = [
            (L["conflicts"], "".join(f"<li>{self.conflict(x)}</li>" for x in self.open_conflicts()) or none),
            (L["questions"], "".join(f"<li>{self.question(q)}</li>" for q in self.open_questions()) or none),
            (L["next"], "".join(f"<li>{s}</li>" for s in self.next_steps()) or none),
            (L["outside"], "".join(f"<li>{self.ref(p)}</li>" for p in people if p not in in_tree) or none),
        ]
        if self.hide_living:
            # Free text of the sessions may name anyone – not in a version for sharing.
            boxes = [b for b in boxes if b[0] != L["next"]]
        return PAGE.format(
            lang=self.lang, W=W, H=H,
            title=esc(f"{self.title} – {L['map']}"),
            heading=esc(self.title),
            sub=f'{esc(L["root"])}: {self.ref(self.root)} · {esc(L["generated"])} {esc(human_date(self.today.isoformat(), self.lang))} · '
                f'<span class="{"ok" if self.report.ok else "bad"}">{esc(check)}</span>'
                + (f' · <b>{esc(L["shared"])}</b>' if self.hide_living else ""),
            chips="".join(f'<span class="chip">{esc(c)}</span>' for c in chips),
            legend_label=esc(L["legend"]),
            cards_label=esc(L["cards"]), legend_cards=legend_cards,
            lines_label=esc(L["lines"]), legend_lines=legend_lines,
            tree_label=esc(L["tree"]), tree_sub=esc(L["tree_sub"]),
            tree=tree,
            boxes="\n".join(f'<section class="box"><h2>{esc(h)}</h2><ul>{body}</ul></section>' for h, body in boxes),
            details=details,
        )


def default_lang(config: dict) -> str:
    """Map language when map.lang is missing: the language of the first known region."""
    for region in config.get("regions") or []:
        if REGION_LANG.get(region) in LABELS:
            return REGION_LANG[region]
    return "en"


def _rank(confidence) -> int:
    return CONFIDENCE.index(confidence) if confidence in CONFIDENCE else len(CONFIDENCE)


def _start(date) -> int:
    return edtf.parse(date)[0] if edtf.is_valid(date) else 99999


def _load_vocab() -> dict[str, dict[str, dict]]:
    out = {}
    for path in sorted((FRAMEWORK / "schema" / "vocab").glob("*.yaml")):
        data = load_yaml(path.read_text(encoding="utf-8")) or {}
        out[data.get("name", path.stem)] = {v["id"]: v for v in data.get("values") or [] if isinstance(v, dict) and "id" in v}
    return out


PAGE = """<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'">
<!-- GENERATED by tools/build_views.py – do not edit, not saved in git (Proavus ADR 0019, 0027) -->
<title>{title}</title>
<style>
:root {{ --bg:#f5f4ef; --fg:#1f1f1c; --muted:#6a6860; --card:#ffffff; --border:#dcd9cd; --chip:#e9e7df;
  --line:#8f8c82; --d3:#2f7d4f; --d2:#2b6cb0; --d1:#c7790b; --d0:#7b4fb8; --n:#7b4fb8; --warn:#c0392b; --liv:#2f7d4f; }}
@media (prefers-color-scheme: dark) {{
  :root {{ --bg:#1b1b19; --fg:#ecebe6; --muted:#a6a398; --card:#262624; --border:#3a3a36; --chip:#33332f; --line:#7d7a70; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
main {{ max-width:1400px; margin:0 auto; padding:24px 16px 56px; }}
h1 {{ font-size:26px; margin:0 0 4px; }}
h2 {{ font-size:18px; margin:0 0 10px; }}
h3 {{ font-size:12px; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); margin:14px 0 6px; }}
.sub {{ color:var(--muted); margin:0 0 14px; font-size:14px; }}
.muted {{ color:var(--muted); }} .ok {{ color:var(--d3); }} .bad {{ color:var(--warn); font-weight:700; }}
code {{ font-size:13px; background:var(--chip); padding:1px 5px; border-radius:4px; }}
a {{ color:var(--d2); }} a.id {{ font-size:11px; color:var(--muted); }}
.chips {{ display:flex; flex-wrap:wrap; gap:8px; margin-bottom:16px; }}
.chip {{ background:var(--chip); border-radius:99px; padding:4px 12px; font-size:13px; }}
.box {{ background:var(--card); border:1px solid var(--border); border-radius:12px; padding:16px 18px; }}
.box ul, .box ol {{ margin:6px 0; padding-left:20px; }}
.box li {{ margin-bottom:6px; }}
.grid {{ display:grid; grid-template-columns:repeat(auto-fit, minmax(min(100%, 320px), 1fr)); gap:14px; margin-top:14px; }}
.legend {{ display:flex; flex-wrap:wrap; gap:10px 20px; font-size:13px; color:var(--muted); margin-bottom:8px; }}
.legend > span {{ display:inline-flex; align-items:center; gap:7px; }}
.legend b {{ color:var(--fg); font-weight:600; width:100%; }}
.sw {{ display:inline-block; width:26px; height:16px; border-radius:4px; background:var(--card);
  border:1px solid var(--border); border-left-width:6px; border-left-style:solid; }}
.sw.src-3 {{ border-left-color:var(--d3); }} .sw.src-2 {{ border-left-color:var(--d2); }}
.sw.src-1 {{ border-left-color:var(--d1); }} .sw.src-0 {{ border-left-color:var(--d0); border-left-style:dashed; }}
.tag {{ padding:0 6px; border-radius:99px; background:var(--chip); color:var(--muted); font-size:10px; line-height:16px; white-space:nowrap; margin-right:3px; }}
.tag.n {{ color:var(--n); }} .card .liv {{ color:var(--liv); }}
.warn {{ color:var(--warn); font-weight:700; font-size:13px; line-height:1; }}
.alt {{ color:var(--d1); font-weight:700; cursor:help; }}
.tree-wrap {{ overflow:auto; border:1px solid var(--border); border-radius:12px; background:var(--card); margin-top:10px; }}
#tree {{ position:relative; }}
#tree svg {{ position:absolute; left:0; top:0; pointer-events:none; }}
.link {{ fill:none; stroke:var(--line); stroke-width:1.6; }}
.link.c-proved {{ stroke-width:2.4; }}
.link.c-probable {{ stroke-dasharray:8 4; }}
.link.c-possible {{ stroke-dasharray:2 4; stroke-linecap:round; }}
.link.c-not-proved {{ stroke-dasharray:1 7; stroke-linecap:round; opacity:.75; }}
.link.n {{ stroke:var(--n); }}
.gen {{ position:absolute; top:14px; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:var(--muted); }}
.card {{ position:absolute; width:{W}px; height:{H}px; margin:0; padding:8px 10px 8px 12px; text-align:left; font:inherit; color:inherit;
  background:var(--card); border:1px solid var(--border); border-left:6px solid var(--c); border-radius:10px; cursor:pointer;
  box-shadow:0 1px 2px rgba(0,0,0,.06); display:flex; flex-direction:column; gap:4px; overflow:hidden; }}
.card:hover, .card:focus-visible {{ outline:none; box-shadow:0 0 0 2px var(--c); }}
.card.src-3 {{ --c:var(--d3); }} .card.src-2 {{ --c:var(--d2); }} .card.src-1 {{ --c:var(--d1); }}
.card.src-0, .card.src-n {{ --c:var(--d0); border-left-style:dashed; }}
.card.nonown {{ border-style:dashed; }}
.card.ph {{ cursor:default; background:transparent; color:var(--muted); }}
.card .top {{ display:flex; justify-content:space-between; align-items:center; min-height:16px; }}
.card .nm {{ font-weight:650; font-size:14px; line-height:1.2; display:-webkit-box; -webkit-line-clamp:2; -webkit-box-orient:vertical; overflow:hidden; }}
.card .dt {{ display:flex; flex-direction:column; font-size:12px; color:var(--muted); line-height:1.35; }}
.card .pl {{ font-size:11px; line-height:1.3; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.card .pf {{ font-size:11px; line-height:1.3; font-style:italic; color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.card .or {{ font-size:11px; line-height:1.3; font-style:italic; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }}
.mar-bg {{ fill:var(--card); stroke:var(--line); stroke-width:1; }}
.mar {{ font-size:11px; fill:var(--fg); text-anchor:middle; dominant-baseline:central; }}
.conf {{ white-space:nowrap; }} .conf svg {{ vertical-align:middle; margin-right:4px; }}
dialog:focus {{ outline:none; }}
dialog {{ border:0; border-radius:14px; padding:0; width:min(640px, calc(100% - 32px)); max-height:calc(100vh - 32px);
  background:var(--card); color:var(--fg); box-shadow:0 20px 50px rgba(0,0,0,.35); }}
dialog::backdrop {{ background:rgba(0,0,0,.45); }}
.dlg {{ padding:22px 24px; overflow-wrap:break-word; }}
.dlg h2 {{ font-size:20px; margin-bottom:4px; }}
.dlg .sub {{ margin-bottom:6px; }}
.dlg dl {{ display:grid; grid-template-columns:150px 1fr; gap:8px 14px; font-size:14px; margin:14px 0; }}
.dlg dt {{ color:var(--muted); }} .dlg dd {{ margin:0; }} .dlg dd > div {{ margin-bottom:4px; }}
.dlg ul.notes {{ padding-left:18px; font-size:14px; }} .dlg ul.notes > li {{ margin-bottom:8px; }}
.src-list {{ font-size:13px; padding-left:18px; }}
.disproved, .disproved a, .disproved .lnk {{ text-decoration:line-through; color:var(--muted); }}
.lnk {{ background:none; border:0; padding:0; font:inherit; color:var(--d2); text-decoration:underline; cursor:pointer; }}
.close {{ margin-top:8px; font:inherit; padding:6px 14px; border-radius:8px; border:1px solid var(--border); background:var(--chip); color:var(--fg); cursor:pointer; }}
@media (max-width:520px) {{ .dlg dl {{ grid-template-columns:1fr; }} .dlg dt {{ margin-top:6px; }} }}
</style>
</head>
<body>
<main>
<h1>{heading}</h1>
<p class="sub">{sub}</p>
<div class="chips">{chips}</div>
<section class="box">
<h2>{legend_label}</h2>
<div class="legend"><b>{cards_label}</b>{legend_cards}</div>
<div class="legend"><b>{lines_label}</b>{legend_lines}</div>
</section>
<section class="box" style="margin-top:14px">
<h2>{tree_label}</h2>
<p class="sub">{tree_sub}</p>
<div class="tree-wrap">
{tree}
</div>
</section>
<div class="grid">
{boxes}
</div>
</main>
<dialog id="dlg" tabindex="-1"><div class="dlg"></div></dialog>
{details}
<script>
(function () {{
  var dlg = document.getElementById("dlg"), box = dlg.querySelector(".dlg");
  function openDetail(id) {{
    var t = document.getElementById("d-" + id);
    if (!t) return;
    box.replaceChildren(t.content.cloneNode(true));
    box.scrollTop = 0;
    if (!dlg.open) dlg.showModal();
    dlg.focus();
    history.replaceState(null, "", "#" + id);
  }}
  document.addEventListener("click", function (e) {{
    var b = e.target.closest("[data-id]");
    if (b) {{ openDetail(b.getAttribute("data-id")); return; }}
    if (e.target.closest(".close") || e.target === dlg) dlg.close();
  }});
  dlg.addEventListener("close", function () {{ history.replaceState(null, "", location.pathname); }});
  if (location.hash) openDetail(decodeURIComponent(location.hash.slice(1)));
}})();
</script>
</body>
</html>
"""


def build_map(repo: Path, out: Path | None = None, root: str | None = None, today: dt.date | None = None,
              hide_living: bool = False) -> tuple[Path, MapBuilder]:
    repo = repo.resolve()
    check_family_repo(repo, "build_views")
    out = (out or repo / "views" / ("mapa-sdileni.html" if hide_living else "mapa.html")).resolve()
    builder = MapBuilder(repo, out, today or dt.date.today(), root, hide_living)
    page = builder.render()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out, builder


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate views of a Proavus family repository.")
    parser.add_argument("repo", nargs="?", default=".", help="family repository (default: .)")
    parser.add_argument("--root", help="starting person ID (default: map.root in repo.yaml)")
    parser.add_argument("--out", help="output file (default: REPO/views/mapa.html, with --hide-living mapa-sdileni.html)")
    parser.add_argument("--hide-living", action="store_true", help="version for sharing outside the family: living persons without names or data")
    args = parser.parse_args(argv)
    repo = Path(args.repo).resolve()
    if args.root and not ids.parse(args.root):
        raise SystemExit(f"build_views: {args.root!r} is not a person ID")
    out, builder = build_map(repo, Path(args.out).resolve() if args.out else None, args.root, hide_living=args.hide_living)
    errors = len(builder.report.errors)
    print(f"{out} written: {len(builder.people)} persons, root {builder.root}"
          + (f" – {errors} validation errors, the map may be incomplete" if errors else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
