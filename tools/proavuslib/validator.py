"""Validate a family repository: headers, IDs, links and research rules.

Each rule of method/rules.md that a machine can check is checked here
(machine → LLM → human, ADR 0005).
"""

from __future__ import annotations

import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import edtf, ids
from .frontmatter import load_yaml, split
from .schemas import SchemaSet

DEFAULT_LIVING_THRESHOLD = 110
MINOR_YEARS = 18
STRONG = ("proved", "probable")
# Facts that may be stored about a living person (ADR 0025).
LIVING_ALLOWED_FACTS = {"name", "sex", "birth"}
BIRTH_FACTS = ("birth", "baptism")
DEATH_FACTS = ("death", "burial")
# Coverage ranges given only as a query (ADR 0035).
QUERY_METHODS = {"database-search", "full-text-search", "index"}
# Question states after which no task for it should stay open (ADR 0047).
CLOSED_QUESTION = ("answered", "bounded", "abandoned")
# A task that looks like a letter or request to an office: an e-mail address or the
# Czech words for answer, inquiry, request in any form (ADR 0047).
EMAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
INQUIRY_WORDS = re.compile(r"\b(odpoved|dotaz|zadost)")
# Sex implied by a participant's role when the record does not state it (ADR 0040).
ROLE_SEX = {
    "father": "male", "groom": "male", "groom-father": "male", "bride-father": "male", "spouse-father": "male",
    "paternal-grandfather": "male", "maternal-grandfather": "male", "grandfather": "male", "godfather": "male",
    "mother": "female", "bride": "female", "groom-mother": "female", "bride-mother": "female", "spouse-mother": "female",
    "paternal-grandmother": "female", "maternal-grandmother": "female", "grandmother": "female", "godmother": "female",
}


@dataclass
class Entity:
    path: Path        # relative to the repository root
    data: dict
    body: str

    @property
    def id(self) -> str:
        return self.data.get("id", "")

    @property
    def type(self) -> str:
        return self.data.get("type", "")


@dataclass
class Report:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    files: int = 0

    def error(self, where, msg):
        self.errors.append(f"{where}: {msg}")

    def warn(self, where, msg):
        self.warnings.append(f"{where}: {msg}")

    def note(self, where, msg):
        self.notes.append(f"{where}: {msg}")

    @property
    def ok(self) -> bool:
        return not self.errors


class RepoValidator:
    def __init__(self, repo_root: Path, framework_root: Path, today: _dt.date | None = None):
        self.root = repo_root
        self.framework_root = framework_root
        self.today = today or _dt.date.today()
        self.report = Report()
        self.entities: dict[str, Entity] = {}
        self.aliases: dict[str, str] = {}
        self.members: set[str] = set()
        self.threshold = DEFAULT_LIVING_THRESHOLD
        self.config: dict = {}

    # ------------------------------------------------------------------ run
    def run(self) -> Report:
        config = self._load_config()
        if config is None:
            return self.report
        self._load_entities()
        self._check_references()
        self._check_records()
        self._check_assertions()
        self._check_relationships()
        self._check_identity_gate()
        self._check_living()
        self._check_dates()
        self._check_identity_sex()
        self._check_duplicate_persons()
        self._check_duplicate_facts()
        self._check_coverage()
        self._check_volumes()
        self._check_sessions()
        self._check_inquiries()
        self._check_map()
        return self.report

    # --------------------------------------------------------------- config
    def _load_config(self) -> dict | None:
        path = self.root / "repo.yaml"
        if not path.is_file():
            self.report.error("repo.yaml", "missing – not a Proavus family repository")
            return None
        try:
            config = load_yaml(path.read_text(encoding="utf-8")) or {}
        except Exception as exc:  # broken YAML
            self.report.error("repo.yaml", f"cannot be read: {exc}")
            return None
        extensions = config.get("extensions") or [] if isinstance(config, dict) else []
        self.schemas = SchemaSet(self.framework_root, extensions)
        for msg in self.schemas.extension_errors:
            self.report.error("repo.yaml", msg)
        errors, _ = self.schemas.validate("repo", config if isinstance(config, dict) else {})
        for msg in errors:
            self.report.error("repo.yaml", msg)
        if not isinstance(config, dict):
            return None
        self.members = {m.get("abbr") for m in config.get("members") or [] if isinstance(m, dict)}
        self.threshold = config.get("living_threshold_years", DEFAULT_LIVING_THRESHOLD)
        self.config = config
        return config

    # ------------------------------------------------------------- entities
    def _load_entities(self) -> None:
        for entity_type, (prefix, dirname) in ids.ENTITIES.items():
            base = self.root / dirname
            if not base.is_dir():
                continue
            for path in sorted(base.rglob("*.md")):
                if path.name.lower() == "readme.md" or path.name.startswith("_"):
                    continue
                self._load_entity(path, entity_type)

    def _load_entity(self, path: Path, expected_type: str) -> None:
        rel = path.relative_to(self.root)
        self.report.files += 1
        try:
            data, body = split(path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            self.report.error(rel, str(exc))
            return
        if not str(rel).isascii():
            self.report.error(rel, "file and directory names must be ASCII")
        entity = Entity(rel, data, body)
        if entity.type != expected_type:
            self.report.error(rel, f"type {entity.type!r} does not belong in {rel.parts[0]}/ (expected {expected_type!r})")
        errors, warnings = self.schemas.validate(expected_type, data)
        for msg in errors:
            self.report.error(rel, msg)
        for msg in warnings:
            self.report.warn(rel, msg)
        id_ = entity.id
        match = ids.parse(id_)
        if match:
            if ids.TYPE_BY_PREFIX[match["prefix"]] != expected_type:
                self.report.error(rel, f"ID prefix {match['prefix']} does not fit type {expected_type!r}")
            if not ids.date_ok(id_):
                self.report.error(rel, f"ID {id_} contains an invalid date")
            if self.members and match["member"] not in self.members:
                self.report.error(rel, f"ID {id_}: member {match['member']!r} is not listed in repo.yaml")
            stem = path.stem
            if stem != id_ and not stem.startswith(id_ + "--"):
                self.report.error(rel, f"file name must be {id_}.md or {id_}--<slug>.md")
            if id_ in self.entities or id_ in self.aliases:
                self.report.error(rel, f"duplicate ID {id_} (also in {self._where(id_)})")
                return
            self.entities[id_] = entity
        for gap in data.get("schema_gap") or []:
            self.report.note(rel, f"schema-gap: {gap}")
        for alias in data.get("aliases") or []:
            if isinstance(alias, dict) and isinstance(alias.get("id"), str):
                if alias["id"] in self.entities:
                    self.report.error(rel, f"alias {alias['id']} still exists as its own file")
                self.aliases[alias["id"]] = id_

    def _where(self, id_: str) -> str:
        if id_ in self.entities:
            return str(self.entities[id_].path)
        return f"alias of {self.aliases[id_]}"

    def _resolve(self, id_: str) -> Entity | None:
        id_ = self.aliases.get(id_, id_)
        return self.entities.get(id_)

    def of_type(self, entity_type: str):
        return [e for e in self.entities.values() if e.type == entity_type]

    # ----------------------------------------------------------- references
    def _check_references(self) -> None:
        for entity in self.entities.values():
            for key_path, value in _strings(entity.data):
                if key_path == "id" or key_path.endswith("aliases.id"):
                    continue
                if ids.parse(value) and self._resolve(value) is None:
                    self.report.error(entity.path, f"{key_path}: link to {value}, which does not exist")

    # -------------------------------------------------------------- records
    def _check_records(self) -> None:
        for rec in self.of_type("record"):
            keys = [p.get("key") for p in rec.data.get("participants") or [] if isinstance(p, dict)]
            dupes = {k for k in keys if keys.count(k) > 1}
            for k in sorted(dupes):
                self.report.error(rec.path, f"participant key {k} is used twice")
            if "## Transcript" not in rec.body:
                self.report.error(rec.path, "body needs a '## Transcript' section (verbatim transcript first)")
            for crop in self.crops(rec):
                if not (self.root / rec.path.parent / crop).is_file():
                    self.report.error(rec.path, f"crop {crop} not found")
            reading = rec.data.get("reading") if isinstance(rec.data.get("reading"), dict) else {}
            confirmed = reading.get("confirmed") if isinstance(reading.get("confirmed"), dict) else {}
            if reading.get("status") == "confirmed" and confirmed.get("by") not in (reading.get("read_by") or []):
                self.report.error(rec.path, f"reading confirmed by {confirmed.get('by')!r}, who is not among the members who read it (read_by) – "
                                            "only a person who read the entry may confirm it (ADR 0033)")

    @staticmethod
    def crops(rec: Entity) -> list[str]:
        """Paths of the evidence crops: crops (ADR 0031) or the short form crop."""
        out = [c.get("path") for c in rec.data.get("crops") or [] if isinstance(c, dict) and isinstance(c.get("path"), str)]
        if isinstance(rec.data.get("crop"), str):
            out.append(rec.data["crop"])
        return out

    def _participant_exists(self, record_id: str, key: str) -> bool:
        rec = self._resolve(record_id)
        if rec is None or rec.type != "record":
            return False
        return any(isinstance(p, dict) and p.get("key") == key for p in rec.data.get("participants") or [])

    def _cited_records(self, assertion: Entity) -> list[Entity]:
        """Records cited by an assertion (or directly by a relationship, ADR 0038)."""
        out = []
        for c in assertion.data.get("citations") or []:
            if isinstance(c, dict) and c.get("record"):
                rec = self._resolve(c["record"])
                if rec is not None:
                    out.append(rec)
        part = assertion.data.get("participant")
        if isinstance(part, dict) and part.get("record"):
            rec = self._resolve(part["record"])
            if rec is not None and rec not in out:
                out.append(rec)
        return out

    @staticmethod
    def _reading(rec: Entity) -> str:
        """Reading state; 'confirmed' only if a member who read the entry confirmed it (ADR 0033)."""
        reading = rec.data.get("reading")
        if not isinstance(reading, dict):
            return ""
        status = reading.get("status", "")
        if status == "confirmed":
            by = reading.get("confirmed", {}).get("by") if isinstance(reading.get("confirmed"), dict) else None
            if by not in (reading.get("read_by") or []):
                return "confirmed by someone who did not read it"
        return status

    # ----------------------------------------------------------- assertions
    def _check_assertions(self) -> None:
        for a in self.of_type("assertion") + self.of_type("relationship"):
            for c in a.data.get("citations") or []:
                if isinstance(c, dict) and c.get("participant"):
                    if not c.get("record"):
                        self.report.error(a.path, "citation names a participant but no record")
                    elif not self._participant_exists(c["record"], c["participant"]):
                        self.report.error(a.path, f"participant {c['participant']} not found in {c['record']}")
            part = a.data.get("participant")
            if a.type == "assertion" and a.data.get("kind") == "identity" and isinstance(part, dict):
                if not self._participant_exists(part.get("record", ""), part.get("key", "")):
                    self.report.error(a.path, f"identity: participant {part.get('key')} not found in {part.get('record')}")

    # -------------------------------------------------------- relationships
    def _check_relationships(self) -> None:
        for rel in self.of_type("relationship"):
            parties = [p for p in rel.data.get("parties") or [] if isinstance(p, dict)]
            roles = [p.get("role") for p in parties]
            kind = rel.data.get("rel_type")
            if kind == "parent-child":
                if roles.count("parent") != 1 or roles.count("child") != 1 or len(parties) != 2:
                    self.report.error(rel.path, "parent-child needs exactly one parent and one child (one file per parent)")
            elif kind == "partnership":
                if roles.count("partner") != 2 or len(parties) != 2:
                    self.report.error(rel.path, "partnership needs exactly two partners")
            for p in parties:
                if p.get("person") == "unknown" and p.get("role") != "parent":
                    self.report.error(rel.path, "only a parent may be 'unknown'")
            for a_id in rel.data.get("assertions") or []:
                a = self._resolve(a_id)
                if a is not None and a.type != "assertion":
                    self.report.error(rel.path, f"{a_id} is not an assertion")

    # -------------------------------------------------------- identity gate
    def _check_identity_gate(self) -> None:
        """A record read only once may not support 'proved' or a merge (ADR 0016)."""
        for a in self.of_type("assertion"):
            conf = a.data.get("confidence")
            identity = a.data.get("kind") == "identity"
            gated = conf == "proved" or (identity and conf in STRONG)
            if not gated:
                continue
            what = "identity link" if identity else "proved assertion"
            if "confirmed" not in a.data:
                self.report.error(a.path, f"{what} needs 'confirmed' (by, on) – the identity gate is passed by a human in the session")
            for rec in self._cited_records(a):
                if self._reading(rec) != "confirmed":
                    self.report.error(a.path, f"{what} relies on {rec.id}, whose reading is {self._reading(rec) or 'missing'} – needs a second reading confirmed by a member who read it")
        for rel in self.of_type("relationship"):
            if rel.data.get("confidence") != "proved":
                continue
            if "confirmed" not in rel.data:
                self.report.error(rel.path, "proved relationship needs 'confirmed' (by, on)")
            support = rel.data.get("assertions") or []
            if not support and not rel.data.get("citations"):
                self.report.error(rel.path, "proved relationship needs supporting assertions or citations")
            for rec in self._cited_records(rel):
                if self._reading(rec) != "confirmed":
                    self.report.error(rel.path, f"proved relationship cites {rec.id}, which is not confirmed by a second reading")
            for a_id in support:
                a = self._resolve(a_id)
                if a is None or a.type != "assertion":
                    continue
                if a.data.get("confidence") not in STRONG:
                    self.report.error(rel.path, f"proved relationship rests on {a_id} with confidence {a.data.get('confidence')!r}")
                for rec in self._cited_records(a):
                    if self._reading(rec) != "confirmed":
                        self.report.error(rel.path, f"proved relationship rests on {rec.id}, which is not confirmed by a second reading")
        for person in self.of_type("person"):
            for alias in person.data.get("aliases") or []:
                if not isinstance(alias, dict):
                    continue
                for a_id in alias.get("basis") or []:
                    a = self._resolve(a_id)
                    if a is None or a.type != "assertion":
                        continue
                    if a.data.get("kind") != "identity" or a.data.get("confidence") not in STRONG:
                        self.report.error(person.path, f"merge of {alias.get('id')}: basis {a_id} must be a probable or proved identity assertion")
                    for rec in self._cited_records(a):
                        if self._reading(rec) != "confirmed":
                            self.report.error(person.path, f"merge of {alias.get('id')} relies on {rec.id}, which is not confirmed by a second reading")

    # ------------------------------------------------------- living persons
    def _facts(self, person_id: str, fact_types) -> list[Entity]:
        out = []
        for a in self.of_type("assertion"):
            if a.data.get("kind") != "fact" or a.data.get("fact_type") not in fact_types:
                continue
            subject = a.data.get("subject")
            if isinstance(subject, str) and self.aliases.get(subject, subject) == person_id:
                if a.data.get("confidence") != "disproved":
                    out.append(a)
        return out

    def _span(self, person_id: str, fact_types) -> tuple[int, int] | None:
        spans = []
        for a in self._facts(person_id, fact_types):
            if edtf.is_valid(a.data.get("date")):
                spans.append(edtf.parse(a.data["date"]))
        if not spans:
            return None
        return min(s[0] for s in spans), min(s[1] for s in spans)

    def _all_facts(self, person_id: str) -> list[Entity]:
        out = []
        for a in self.of_type("assertion"):
            subject = a.data.get("subject")
            if a.data.get("kind") == "fact" and isinstance(subject, str) and self.aliases.get(subject, subject) == person_id:
                out.append(a)
        return out

    def is_living(self, person: Entity) -> bool:
        status = person.data.get("vital_status")
        if status == "living":
            return True
        if status == "deceased" or self._facts(person.id, DEATH_FACTS):
            return False
        birth = self._span(person.id, BIRTH_FACTS)
        return birth is not None and birth[1] > self.today.year - self.threshold

    def is_minor(self, person: Entity) -> bool:
        """Living and born less than 18 years ago (by the latest reading of the date)."""
        if not self.is_living(person):
            return False
        birth = self._span(person.id, BIRTH_FACTS)
        return birth is not None and birth[1] > self.today.year - MINOR_YEARS

    def _check_living(self) -> None:
        for person in self.of_type("person"):
            unknown = person.data.get("vital_status") == "unknown"
            birth, death = self._span(person.id, BIRTH_FACTS), self._facts(person.id, DEATH_FACTS)
            if unknown and birth is None and not death:
                self.report.warn(person.path, "vital status unknown and no birth date – cannot tell if the person may be living. "
                                              "Add a birth or baptism assertion (an estimate is enough, e.g. 1880~ from an age at marriage), "
                                              "a death or burial assertion, or set vital_status: deceased if the person is known to be dead")
            elif unknown and not death and birth is not None and birth[1] > self.today.year - self.threshold:
                self.report.warn(person.path, f"vital status unknown, born {birth[0]}–{birth[1]} – treated as living (only name, sex, birth "
                                              "and relationships may be stored). If the person died, add a death or burial assertion or set "
                                              "vital_status: deceased; if alive, set vital_status: living")
            if not self.is_living(person):
                continue
            for a in self._all_facts(person.id):
                if a.data.get("fact_type") not in LIVING_ALLOWED_FACTS:
                    self.report.error(a.path, f"{person.id} is (presumed) living: only {', '.join(sorted(LIVING_ALLOWED_FACTS))} may be stored")
            if self.is_minor(person):
                for a in self._facts(person.id, BIRTH_FACTS):
                    if a.data.get("date") is not None:
                        self.report.error(a.path, f"{person.id} is (presumed) a living minor: store the relationship only, no birth date")

    # ---------------------------------------------------------------- dates
    def _check_dates(self) -> None:
        for person in self.of_type("person"):
            pid = person.id
            birth = self._span(pid, BIRTH_FACTS)
            death = self._span(pid, DEATH_FACTS)
            marriage = self._span(pid, ("marriage",))
            if birth and death and death[1] < birth[0]:
                self.report.error(person.path, "dies before being born (check the dates of the birth/death assertions)")
            if birth and death and death[0] - birth[1] > 120:
                self.report.error(person.path, "lifespan over 120 years")
            if birth and marriage and marriage[1] < birth[0] + 12:
                self.report.error(person.path, "marriage before the age of 12")
            if death and marriage and marriage[0] > death[1]:
                self.report.error(person.path, "marriage after death")
        for rel in self.of_type("relationship"):
            if rel.data.get("rel_type") != "parent-child" or rel.data.get("subtype") not in (None, "biological", "legitimated", "presumed"):
                continue
            parties = {p.get("role"): p.get("person") for p in rel.data.get("parties") or [] if isinstance(p, dict)}
            parent, child = parties.get("parent"), parties.get("child")
            if not isinstance(parent, str) or parent == "unknown" or not isinstance(child, str):
                continue
            p_birth, c_birth = self._span(parent, BIRTH_FACTS), self._span(child, BIRTH_FACTS)
            p_death = self._span(parent, DEATH_FACTS)
            if p_birth and c_birth and c_birth[1] < p_birth[0] + 12:
                self.report.error(rel.path, "parent younger than 12 at the child's birth")
            if p_birth and c_birth and c_birth[0] - p_birth[1] > 70:
                self.report.warn(rel.path, "parent older than 70 at the child's birth")
            parent_entity = self._resolve(parent)
            sex = parent_entity.data.get("sex") if parent_entity else None
            if p_death and c_birth:
                if sex == "female" and p_death[1] < c_birth[0]:
                    self.report.error(rel.path, "mother died before the child's birth")
                if sex != "female" and p_death[1] < c_birth[0] - 1:
                    self.report.error(rel.path, "father died more than a year before the child's birth")

    # ------------------------------------------------- identity, duplicates
    def _check_identity_sex(self) -> None:
        """A participant's sex (stated, or implied by the role) must fit the person (ADR 0040)."""
        for a in self.of_type("assertion"):
            part = a.data.get("participant")
            if a.data.get("kind") != "identity" or not isinstance(part, dict):
                continue
            rec, person = self._resolve(part.get("record", "")), self._resolve(a.data.get("person", ""))
            if rec is None or person is None:
                continue
            p = next((x for x in rec.data.get("participants") or [] if isinstance(x, dict) and x.get("key") == part.get("key")), None)
            if p is None:
                continue
            stated = p.get("sex") if p.get("sex") in ("male", "female") else None
            sex = stated or ROLE_SEX.get(p.get("role"))
            if sex and person.data.get("sex") in ("male", "female") and sex != person.data["sex"]:
                why = f"sex {sex}" if stated else f"role {p.get('role')}"
                msg = (f"participant {part.get('key')} of {rec.id} ({why}) does not fit {person.id}, who is {person.data['sex']} – "
                       "check the reading and the link")
                (self.report.error if a.data.get("confidence") in STRONG else self.report.warn)(a.path, msg)

    @staticmethod
    def _name_key(name: str) -> str:
        decomposed = unicodedata.normalize("NFKD", name)
        return " ".join("".join(c for c in decomposed if not unicodedata.combining(c)).casefold().split())

    def _check_duplicate_persons(self) -> None:
        """Same name and an overlapping birth: perhaps one person in two files (ADR 0040)."""
        by_name: dict[str, list[Entity]] = {}
        for person in sorted(self.of_type("person"), key=lambda p: p.id):
            keys = {self._name_key(n.get("value", "")) for n in person.data.get("names") or [] if isinstance(n, dict) and n.get("value")}
            for key in keys:
                by_name.setdefault(key, []).append(person)
        seen: set[tuple[str, str]] = set()
        for key, people in by_name.items():
            for i, a in enumerate(people):
                for b in people[i + 1:]:
                    pair = (a.id, b.id)
                    if pair in seen or b.id in (a.data.get("distinct_from") or []) or a.id in (b.data.get("distinct_from") or []):
                        continue
                    sa, sb = self._span(a.id, BIRTH_FACTS), self._span(b.id, BIRTH_FACTS)
                    if sa is None or sb is None or sa[0] > sb[1] or sb[0] > sa[1]:
                        continue
                    seen.add(pair)
                    self.report.warn(a.path, f"may be the same person as {b.id} (same name, birth {sa[0]}–{sa[1]} and {sb[0]}–{sb[1]}) – "
                                             "merge them with aliases after the identity gate, or add distinct_from if they are namesakes")

    def _check_duplicate_facts(self) -> None:
        """Two assertions of the same type, date and value about one person: join their citations (ADR 0040)."""
        groups: dict[tuple, list[Entity]] = {}
        for a in sorted(self.of_type("assertion"), key=lambda a: a.id):
            d = a.data
            if d.get("kind") != "fact" or d.get("date") is None or d.get("confidence") == "disproved":
                continue
            subject = self.aliases.get(d.get("subject"), d.get("subject"))
            groups.setdefault((subject, d.get("fact_type"), str(d.get("date")), str(d.get("value", ""))), []).append(a)
        for (subject, fact_type, date, _), same in groups.items():
            if len(same) > 1:
                self.report.warn(same[0].path, f"{len(same)} {fact_type} assertions about {subject} with the same date {date} "
                                               f"({', '.join(a.id for a in same)}) – join their citations into one assertion")

    # ------------------------------------------------------------- coverage
    def _check_coverage(self) -> None:
        index_only: list[Entity] = []
        for cov in sorted(self.of_type("coverage"), key=lambda c: c.id):
            result, method = cov.data.get("result"), cov.data.get("method")
            for r in cov.data.get("ranges") or []:
                if isinstance(r, dict) and r.get("query") and not (r.get("dates") or r.get("pages")) and method not in QUERY_METHODS:
                    self.report.error(cov.path, f"a range given only as a query fits a database search ({', '.join(sorted(QUERY_METHODS))}), not method {method!r} – add dates or pages")
            accepted = cov.data.get("index_negative_accepted")
            if result == "negative" and method == "index" and not accepted:
                index_only.append(cov)
            elif accepted and not (result == "negative" and method == "index"):
                self.report.warn(cov.path, "index_negative_accepted only fits a negative result from an index (method index, result negative)")
            if result in ("found", "partial") and not cov.data.get("found"):
                self.report.warn(cov.path, f"result {result!r} but no records listed in 'found'")
            if cov.data.get("inquiry") and method != "inquiry":
                self.report.warn(cov.path, "links an inquiry but method is not 'inquiry'")
        if index_only:
            # One warning for all of them (ADR 0040): a list, not a wall of the same sentence.
            self.report.warn("coverage/", f"{len(index_only)} negative result{'s' if len(index_only) > 1 else ''} from an index only "
                             f"({', '.join(c.id for c in index_only)}) – an index is not proof of absence; page through the book if it "
                             "matters, or record the decision in the file: index_negative_accepted: {by, on, note}")

    # -------------------------------------------------------------- volumes
    @staticmethod
    def _volume_key(value) -> str:
        return str(value).strip().casefold()

    def _check_volumes(self) -> None:
        """Volumes of records and coverage must be volumes their source lists (ADR 0058)."""
        listed: dict[str, list[str]] = {}
        for src in self.of_type("source"):
            vols = [v.get("volume") for v in src.data.get("volumes") or [] if isinstance(v, dict) and v.get("volume") is not None]
            keys = [self._volume_key(v) for v in vols]
            for k in sorted({k for k in keys if keys.count(k) > 1}):
                self.report.error(src.path, f"volume {k!r} is listed twice in volumes")
            if vols:
                listed[src.id] = vols
        for rec in self.of_type("record"):
            vols = listed.get(rec.data.get("source"))
            if not vols:
                continue
            loc = rec.data.get("locator") if isinstance(rec.data.get("locator"), dict) else {}
            if loc.get("volume") is None:
                self.report.warn(rec.path, f"{rec.data.get('source')} has volumes ({', '.join(map(str, vols))}) – add locator.volume")
            elif self._volume_key(loc["volume"]) not in {self._volume_key(v) for v in vols}:
                self.report.error(rec.path, f"locator.volume {loc['volume']!r} is not one of the volumes of {rec.data.get('source')} "
                                            f"({', '.join(map(str, vols))})")
        for cov in self.of_type("coverage"):
            vols = listed.get(cov.data.get("source"))
            if not vols:
                continue
            for r in cov.data.get("ranges") or []:
                if not isinstance(r, dict) or r.get("volume") is None:
                    continue
                if self._volume_key(r["volume"]) not in {self._volume_key(v) for v in vols}:
                    self.report.error(cov.path, f"range volume {r['volume']!r} is not one of the volumes of {cov.data.get('source')} "
                                                f"({', '.join(map(str, vols))})")

    # ------------------------------------------------------------- sessions
    def _check_sessions(self) -> None:
        for s in self.of_type("session"):
            date = s.data.get("date")
            parts = s.path.parts
            if isinstance(date, str) and len(parts) >= 3 and parts[1] != date[:4]:
                self.report.error(s.path, f"session dated {date} belongs in sessions/{date[:4]}/")
            if len(parts) < 3:
                self.report.error(s.path, "sessions are stored by year: sessions/YYYY/")
            for task in s.data.get("human_tasks") or []:
                self._check_task(s, task)

    def _check_task(self, s: Entity, task) -> None:
        """An open human task (ADR 0047): not for a closed question; a letter or request is an inquiry."""
        if isinstance(task, str):
            task = {"task": task, "status": "open"}
        if not isinstance(task, dict) or task.get("status") != "open":
            return
        text = str(task.get("task", ""))
        q = self._resolve(task.get("question")) if isinstance(task.get("question"), str) else None
        if q is not None and q.data.get("status") in CLOSED_QUESTION:
            self.report.warn(s.path, f"open task {clip(text)!r} is for question {q.id}, which is {q.data['status']} – "
                             "close the task (status done or dropped, by, on) or point it to an open question")
        if not task.get("inquiry") and (EMAIL.search(text) or INQUIRY_WORDS.search(_plain(text))):
            self.report.warn(s.path, f"open task {clip(text)!r} looks like a letter or request to an office – "
                             "consider an inquiry (inquiries/, ADR 0036) with addressee, date sent and state, "
                             "and link it from the task as inquiry")

    # ------------------------------------------------------------ inquiries
    def _check_inquiries(self) -> None:
        for inq in self.of_type("inquiry"):
            dates = [(k, inq.data.get(k)) for k in ("sent", "acknowledged", "answered") if isinstance(inq.data.get(k), str)]
            for (k1, d1), (k2, d2) in zip(dates, dates[1:]):
                if d2 < d1:
                    self.report.error(inq.path, f"{k2} {d2} is before {k1} {d1}")
            if isinstance(inq.data.get("sent"), str) and inq.data["sent"] > self.today.isoformat():
                self.report.error(inq.path, f"sent {inq.data['sent']} is in the future")

    # ------------------------------------------------------------------ map
    def _check_map(self) -> None:
        root = (self.config.get("map") or {}).get("root") if isinstance(self.config.get("map"), dict) else None
        if not isinstance(root, str) or not ids.parse(root):
            return
        person = self._resolve(root)
        if person is None or person.type != "person":
            self.report.error("repo.yaml", f"map.root: {root} is not a person in people/")


def _plain(text: str) -> str:
    """Lower case without diacritics, for matching words."""
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def clip(text: str, n: int = 60) -> str:
    return text if len(text) <= n else text[: n - 1] + "…"


def _strings(data, prefix=""):
    """Yield (dotted key path, string value) for every string in a header."""
    if isinstance(data, dict):
        for k, v in data.items():
            yield from _strings(v, f"{prefix}.{k}" if prefix else str(k))
    elif isinstance(data, list):
        for v in data:
            yield from _strings(v, prefix)
    elif isinstance(data, str):
        yield prefix, data
