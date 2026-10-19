"""Validate a family repository: headers, IDs, links and research rules.

Each rule of method/rules.md that a machine can check is checked here
(machine → LLM → human, ADR 0005).
"""

from __future__ import annotations

import datetime as _dt
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
        self._check_coverage()
        self._check_sessions()
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
            crop = rec.data.get("crop")
            if isinstance(crop, str) and not (self.root / rec.path.parent / crop).is_file():
                self.report.error(rec.path, f"crop {crop} not found")

    def _participant_exists(self, record_id: str, key: str) -> bool:
        rec = self._resolve(record_id)
        if rec is None or rec.type != "record":
            return False
        return any(isinstance(p, dict) and p.get("key") == key for p in rec.data.get("participants") or [])

    def _cited_records(self, assertion: Entity) -> list[Entity]:
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
        reading = rec.data.get("reading")
        return reading.get("status", "") if isinstance(reading, dict) else ""

    # ----------------------------------------------------------- assertions
    def _check_assertions(self) -> None:
        for a in self.of_type("assertion"):
            for c in a.data.get("citations") or []:
                if isinstance(c, dict) and c.get("participant"):
                    if not c.get("record"):
                        self.report.error(a.path, "citation names a participant but no record")
                    elif not self._participant_exists(c["record"], c["participant"]):
                        self.report.error(a.path, f"participant {c['participant']} not found in {c['record']}")
            part = a.data.get("participant")
            if a.data.get("kind") == "identity" and isinstance(part, dict):
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
                    self.report.error(a.path, f"{what} relies on {rec.id}, which is {self._reading(rec) or 'not'} read – needs a confirmed second reading")
        for rel in self.of_type("relationship"):
            if rel.data.get("confidence") != "proved":
                continue
            if "confirmed" not in rel.data:
                self.report.error(rel.path, "proved relationship needs 'confirmed' (by, on)")
            support = rel.data.get("assertions") or []
            if not support:
                self.report.error(rel.path, "proved relationship needs supporting assertions")
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

    def _check_living(self) -> None:
        for person in self.of_type("person"):
            if person.data.get("vital_status") == "unknown" and self._span(person.id, BIRTH_FACTS) is None and not self._facts(person.id, DEATH_FACTS):
                self.report.warn(person.path, "vital status unknown and no birth date – cannot tell if the person may be living")
            if not self.is_living(person):
                continue
            for a in self._all_facts(person.id):
                if a.data.get("fact_type") not in LIVING_ALLOWED_FACTS:
                    self.report.error(a.path, f"{person.id} is (presumed) living: only {', '.join(sorted(LIVING_ALLOWED_FACTS))} may be stored")
            birth = self._span(person.id, BIRTH_FACTS)
            if birth is not None and birth[1] > self.today.year - MINOR_YEARS:
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

    # ------------------------------------------------------------- coverage
    def _check_coverage(self) -> None:
        for cov in self.of_type("coverage"):
            result, method = cov.data.get("result"), cov.data.get("method")
            if result == "negative" and method == "index":
                self.report.warn(cov.path, "negative from an index only – an index is not proof of absence; page through the book if it matters")
            if result in ("found", "partial") and not cov.data.get("found"):
                self.report.warn(cov.path, f"result {result!r} but no records listed in 'found'")

    # ------------------------------------------------------------- sessions
    def _check_sessions(self) -> None:
        for s in self.of_type("session"):
            date = s.data.get("date")
            parts = s.path.parts
            if isinstance(date, str) and len(parts) >= 3 and parts[1] != date[:4]:
                self.report.error(s.path, f"session dated {date} belongs in sessions/{date[:4]}/")
            if len(parts) < 3:
                self.report.error(s.path, "sessions are stored by year: sessions/YYYY/")


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
