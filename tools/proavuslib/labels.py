"""Names of entities for people: a person's name, a question's title, a record in words (ADR 0039).

Used by START-HERE, which is read in the family's own sessions; the family map
(build_views.py) has its own labels with the rules for sharing.
"""

from __future__ import annotations

from pathlib import Path

from .dates import human_date
from .frontmatter import load_yaml


def load_vocab(framework_root: Path) -> dict[str, dict[str, dict]]:
    out = {}
    for path in sorted((framework_root / "schema" / "vocab").glob("*.yaml")):
        data = load_yaml(path.read_text(encoding="utf-8")) or {}
        out[data.get("name", path.stem)] = {v["id"]: v for v in data.get("values") or [] if isinstance(v, dict) and "id" in v}
    return out


class Labeler:
    def __init__(self, validator, framework_root: Path, lang: str = "en"):
        self.v = validator
        self.lang = lang
        self.vocab = load_vocab(framework_root)

    def get(self, id_):
        if not isinstance(id_, str):
            return None
        return self.v.entities.get(self.v.aliases.get(id_, id_))

    def term(self, vocab: str, value) -> str:
        entry = self.vocab.get(vocab, {}).get(value)
        return str((entry or {}).get(self.lang) or (entry or {}).get("en") or value or "")

    def name(self, pid) -> str:
        person = self.get(pid)
        names = [n for n in (person.data.get("names") if person else None) or [] if isinstance(n, dict) and n.get("value")]
        names.sort(key=lambda n: not n.get("preferred"))
        return str(names[0]["value"]) if names else str(pid)

    def place(self, place_id, as_written="") -> str:
        place = self.get(place_id)
        if place is not None:
            names = [n for n in place.data.get("names") or [] if isinstance(n, dict)]
            return str(names[0].get("value")) if names else place.id
        return str(as_written or "")

    def record(self, rec) -> str:
        event = rec.data.get("event") if isinstance(rec.data.get("event"), dict) else {}
        head = " ".join(x for x in (self.term("event_types", event.get("type")), human_date(event.get("date"), self.lang)) if x)
        text = ", ".join(x for x in (head, self.place(event.get("place"), event.get("place_as_written", ""))) if x) or rec.id
        principal = next((p.get("name_as_written") for p in rec.data.get("participants") or []
                          if isinstance(p, dict) and p.get("role") == "principal" and p.get("name_as_written")), "")
        return text + (f" („{principal}“)" if principal else "")

    def label(self, id_or_entity) -> str:
        """Plain-text name of any entity – what a person reads instead of the ID."""
        e = id_or_entity if hasattr(id_or_entity, "data") else self.get(id_or_entity)
        if e is None:
            return str(id_or_entity)
        d = e.data
        if e.type == "person":
            return self.name(e.id)
        if e.type == "record":
            return self.record(e)
        if e.type in ("question", "source", "decision"):
            return str(d.get("title") or e.id)
        if e.type == "assertion":
            if d.get("kind") == "identity":
                return f"identity: {self.name(d.get('person'))}"
            when = human_date(d.get("date"), self.lang) if d.get("date") is not None else ""
            return " ".join(x for x in (self.term("fact_types", d.get("fact_type")), when) if x) + f" – {self.label(d.get('subject'))}"
        if e.type == "relationship":
            names = " – ".join("unknown parent" if p.get("person") == "unknown" else self.name(p.get("person"))
                               for p in d.get("parties") or [] if isinstance(p, dict))
            return f"{names} ({self.term('relationship_types', d.get('rel_type'))})"
        if e.type == "conflict":
            about = ", ".join(self.label(a) for a in d.get("about") or [])
            return f"conflict about {about}" if about else "conflict"
        if e.type == "inquiry":
            return f"{d.get('addressee', '')}: {d.get('subject', '')}".strip(": ")
        if e.type == "place":
            return self.place(e.id)
        if e.type == "session":
            return f"session {human_date(d.get('date'), self.lang)}"
        if e.type == "coverage":
            return f"search in {self.label(d.get('source'))}"
        if e.type == "oral":
            return f"oral testimony {human_date(d.get('date'), self.lang)}"
        return e.id

    def ref(self, id_or_entity) -> str:
        """Name followed by the ID, for Markdown: Matěj Pokusný (P-…)."""
        e = id_or_entity if hasattr(id_or_entity, "data") else self.get(id_or_entity)
        id_ = e.id if e is not None else str(id_or_entity)
        label = self.label(e if e is not None else id_or_entity)
        return f"{label} ({id_})" if label != id_ else id_
