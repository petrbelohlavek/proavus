"""Create many entities at once from a plan: symbolic keys, @key links, new IDs (ADR 0042).

A plan lists entities with a symbolic `key` instead of an ID. Every `@key`
– a whole string in the header, or a word in the body – becomes the ID the
entity gets. Nothing is written until the whole batch passes the validator
in a temporary copy of the repository, and no existing file is overwritten.

    batch = Batch(repo, "ab", framework_root)
    batch.add("matej", "person", {"names": [...], "sex": "male", "vital_status": "deceased"})
    batch.add("rel", "relationship", {"rel_type": "parent-child", "parties": [
        {"role": "parent", "person": "@matej"}, {"role": "child", "person": "@josef"}], ...})
    report = batch.preview()      # validator report of the repository with the batch
    paths = batch.write()         # only if preview() has no errors
"""

from __future__ import annotations

import datetime as _dt
import re
import shutil
import tempfile
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

from . import ids
from .frontmatter import join, load_yaml
from .validator import RepoValidator

KEY = r"[a-z0-9][a-z0-9_.-]*"
FULL_REF = re.compile(rf"^@({KEY})$")
BODY_REF = re.compile(rf"(?<![\w@])@({KEY})")
RESERVED = {"key", "slug", "body", "from_diary"}
# What a temporary copy needs for the validator.
COPY_FOR_CHECK = ["repo.yaml"] + sorted({d for _, d in ids.ENTITIES.values()})


class BulkError(Exception):
    pass


@dataclass
class Planned:
    key: str
    type: str
    data: dict
    body: str = ""
    slug: str | None = None
    from_diary: list[str] = field(default_factory=list)
    id: str = ""


def slugify(text: str) -> str:
    """ASCII slug for a file name: Matěj Pokusný → matej-pokusny."""
    plain = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", plain.lower()).strip("-")[:60]


class Batch:
    def __init__(self, repo: Path, member: str, framework_root: Path, today: _dt.date | None = None,
                 known_keys: dict[str, str] | None = None):
        if not re.fullmatch(r"[a-z]{2,4}", member or ""):
            raise BulkError(f"member must be the 2–4 letter abbreviation from repo.yaml, got {member!r}")
        self.repo = repo
        self.member = member
        self.framework_root = framework_root
        self.today = today or _dt.date.today()
        self.known = dict(known_keys or {})          # keys of earlier batches → IDs
        self.items: list[Planned] = []
        self.diary: dict[str, str] = {}               # diary reference → original text
        self._existing = self._ids_in_repo()

    # ------------------------------------------------------------- building
    def _ids_in_repo(self) -> set[str]:
        out = set()
        for _, folder in ids.ENTITIES.values():
            for path in (self.repo / folder).rglob("*.md") if (self.repo / folder).is_dir() else []:
                out.add(path.stem.split("--")[0])
        return out

    def add(self, key: str, entity_type: str, fields: dict, body: str = "", slug: str | None = None,
            from_diary=()) -> str:
        """Plan one entity; returns its new ID."""
        if not re.fullmatch(KEY, key or ""):
            raise BulkError(f"key {key!r}: use lowercase letters, digits, - _ . (e.g. matej, bapt-josef-1878)")
        if key in self.known or any(p.key == key for p in self.items):
            raise BulkError(f"key {key!r} is used twice")
        if entity_type not in ids.ENTITIES:
            raise BulkError(f"{key}: unknown type {entity_type!r} – one of {', '.join(sorted(ids.ENTITIES))}")
        if "id" in fields:
            raise BulkError(f"{key}: no id – the batch gives every entity a new ID; link it as @{key}")
        taken = self._existing | set(self.known.values()) | {p.id for p in self.items}
        new = ids.new_id(entity_type, self.member, taken, self.today)
        self.items.append(Planned(key, entity_type, dict(fields), body or "", slug, list(from_diary), new))
        return new

    def add_diary(self, ref: str, text: str) -> None:
        """An entry of the old research diary; every one must be linked by some entity (from_diary)."""
        if ref in self.diary:
            raise BulkError(f"diary entry {ref!r} is listed twice")
        self.diary[ref] = text

    def key_map(self) -> dict[str, str]:
        return {**self.known, **{p.key: p.id for p in self.items}}

    # ------------------------------------------------------------ resolving
    def _resolve(self, value, where: str):
        keys = self.key_map()
        if isinstance(value, str):
            m = FULL_REF.match(value)
            if m:
                if m.group(1) not in keys:
                    raise BulkError(f"{where}: @{m.group(1)} – no entity with this key")
                return keys[m.group(1)]
            return BODY_REF.sub(lambda w: keys.get(w.group(1), w.group(0)), value)   # @key inside a sentence
        if isinstance(value, list):
            return [self._resolve(v, where) for v in value]
        if isinstance(value, dict):
            return {k: self._resolve(v, f"{where}.{k}") for k, v in value.items()}
        return value

    def _body(self, p: Planned) -> str:
        keys = self.key_map()

        def swap(m):
            return keys.get(m.group(1), m.group(0))   # an unknown @word stays (e-mail, handle)

        body = BODY_REF.sub(swap, p.body.strip("\n"))
        quotes = [f"> {ref}: " + self.diary[ref].replace("\n", "\n> ") for ref in p.from_diary if ref in self.diary]
        if quotes:
            body = (body + "\n\n" if body else "") + "## From the old research diary\n\n" + "\n>\n".join(quotes)
        return "\n" + body + "\n" if body else "\n"

    def _header(self, p: Planned) -> dict:
        data = self._resolve({k: v for k, v in p.data.items() if k not in RESERVED | {"type"}}, p.key)
        return {"id": p.id, "type": p.type, **data}

    def _relpath(self, p: Planned, header: dict) -> Path:
        folder = ids.ENTITIES[p.type][1]
        if p.type == "session":
            date = str(header.get("date") or "")
            if not re.match(r"^[0-9]{4}-", date):
                raise BulkError(f"{p.key}: a session needs date: YYYY-MM-DD (it goes into sessions/YYYY/)")
            folder = f"{folder}/{date[:4]}"
        slug = slugify(p.slug) if p.slug else ""
        return Path(folder) / (f"{p.id}--{slug}.md" if slug else f"{p.id}.md")

    def files(self) -> list[tuple[Path, str]]:
        """(relative path, file text) of every planned entity, links resolved."""
        out = []
        for p in self.items:
            header = self._header(p)
            out.append((self._relpath(p, header), join(header, self._body(p))))
        return out

    def missing_diary(self) -> list[str]:
        """Diary entries no entity refers to (from_diary) – nothing of the old diary may get lost."""
        linked = {ref for p in self.items for ref in p.from_diary}
        unknown = sorted(linked - set(self.diary))
        if unknown:
            raise BulkError(f"from_diary names entries that are not in the diary: {', '.join(unknown)}")
        return [ref for ref in self.diary if ref not in linked]

    # --------------------------------------------------------------- output
    def preview(self):
        """Validator report of the repository as it would be with the batch (nothing is written)."""
        files = self.files()
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            copy.mkdir()
            for name in COPY_FOR_CHECK:
                src = self.repo / name
                if src.is_dir():
                    shutil.copytree(src, copy / name)
                elif src.is_file():
                    shutil.copy2(src, copy / name)
            for rel, text in files:
                (copy / rel).parent.mkdir(parents=True, exist_ok=True)
                (copy / rel).write_text(text, encoding="utf-8")
            return RepoValidator(copy, self.framework_root, today=self.today).run()

    def write(self) -> list[Path]:
        """Write the batch into the repository; refuses if the validator finds errors or a file exists."""
        report = self.preview()
        if report.errors:
            raise BulkError(f"the batch has {len(report.errors)} validation errors – nothing written:\n  " + "\n  ".join(report.errors[:20]))
        files = self.files()
        for rel, _ in files:
            if (self.repo / rel).exists():
                raise BulkError(f"{rel} already exists – nothing written")
        written = []
        for rel, text in files:
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_text(text, encoding="utf-8")
            written.append(self.repo / rel)
        return written


def load_plan(path: Path) -> dict:
    """Read a plan file (YAML): member, entities (each with key and type), diary."""
    data = load_yaml(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict) or not isinstance(data.get("entities"), list):
        raise BulkError(f"{path}: a plan needs 'entities:' – a list of entities with key and type")
    return data


def batch_from_plan(plan: dict, repo: Path, framework_root: Path, member: str | None = None,
                    today: _dt.date | None = None, known_keys: dict[str, str] | None = None) -> Batch:
    batch = Batch(repo, member or plan.get("member"), framework_root, today, known_keys)
    for entry in plan.get("diary") or []:
        if not isinstance(entry, dict) or "ref" not in entry or "text" not in entry:
            raise BulkError("each diary entry needs ref and text")
        batch.add_diary(str(entry["ref"]), str(entry["text"]).strip())
    for n, entry in enumerate(plan["entities"], start=1):
        if not isinstance(entry, dict) or "key" not in entry or "type" not in entry:
            raise BulkError(f"entity {n} needs key and type")
        fields = {k: v for k, v in entry.items() if k not in RESERVED | {"type"}}
        from_diary = entry.get("from_diary") or []
        batch.add(str(entry["key"]), str(entry["type"]), fields, str(entry.get("body") or ""),
                  entry.get("slug"), [str(x) for x in (from_diary if isinstance(from_diary, list) else [from_diary])])
    return batch
