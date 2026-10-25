"""Load the JSON Schemas, vocabularies and regional extensions (ADR 0015)."""

from __future__ import annotations

import copy
import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker, ValidationError, validators
from referencing import Registry, Resource

from . import edtf
from .frontmatter import load_yaml

VOCAB_KEYWORD = "x-vocab"


class SchemaSet:
    """Schemas for one family repository (core + switched-on extensions)."""

    def __init__(self, framework_root: Path, extensions: list[str] | None = None):
        self.schema_dir = framework_root / "schema"
        self.regions_dir = framework_root / "regions"
        self.schemas: dict[str, dict] = {}
        for path in sorted(self.schema_dir.glob("*.schema.json")):
            name = path.name.removesuffix(".schema.json")
            self.schemas[name] = json.loads(path.read_text(encoding="utf-8"))
        self.vocab: dict[str, set[str]] = {}
        for path in sorted((self.schema_dir / "vocab").glob("*.yaml")):
            data = load_yaml(path.read_text(encoding="utf-8"))
            self.vocab[data["name"]] = {v["id"] for v in data.get("values", [])}
        self.extension_errors: list[str] = []
        for ext in extensions or []:
            self._apply_extension(ext)
        self._build()

    def _apply_extension(self, name: str) -> None:
        path = self.regions_dir / name / "schema-ext.yaml"
        if not path.is_file():
            self.extension_errors.append(f"extension {name!r} not found ({path.name} in regions/{name}/)")
            return
        data = load_yaml(path.read_text(encoding="utf-8")) or {}
        for target, fields in (data.get("fields") or {}).items():
            entity, _, defname = target.partition("#")
            schema = self.schemas.get(entity)
            if schema is None:
                self.extension_errors.append(f"extension {name!r}: unknown entity {entity!r}")
                continue
            node = schema["$defs"].get(defname) if defname else schema
            if node is None:
                self.extension_errors.append(f"extension {name!r}: unknown target {target!r}")
                continue
            props = node.setdefault("properties", {})
            for field, definition in fields.items():
                if field in props and props[field] != definition:
                    # Two regions may share a field (e.g. domicile in cz and at), never redefine it.
                    self.extension_errors.append(f"extension {name!r}: {target}.{field} is already defined differently")
                    continue
                props[field] = copy.deepcopy(definition)
        for vocab_name, values in (data.get("vocab") or {}).items():
            self.vocab.setdefault(vocab_name, set()).update(v["id"] for v in values)

    def _build(self) -> None:
        resources = [(s["$id"], Resource.from_contents(s)) for s in self.schemas.values()]
        self.registry = Registry().with_resources(resources)
        vocab = self.vocab

        def check_vocab(validator, vocab_name, instance, schema):
            if isinstance(instance, str) and instance not in vocab.get(vocab_name, set()):
                yield ValidationError(
                    f"unknown value {instance!r} in vocabulary {vocab_name} – "
                    f"add it to the vocabulary if it is a real new case",
                    validator=VOCAB_KEYWORD,
                )

        checker = FormatChecker()
        checker.checks("edtf")(edtf.is_valid)
        cls = validators.extend(Draft202012Validator, {VOCAB_KEYWORD: check_vocab})
        self._validators = {
            name: cls(schema, registry=self.registry, format_checker=checker)
            for name, schema in self.schemas.items()
        }

    def validate(self, entity_type: str, data: dict) -> tuple[list[str], list[str]]:
        """Return (errors, warnings) for one header."""
        validator = self._validators.get(entity_type)
        if validator is None:
            return [f"unknown type {entity_type!r}"], []
        errors, warnings = [], []
        for err in validator.iter_errors(data):
            where = err.json_path.removeprefix("$").lstrip(".") or "(header)"
            if err.validator in ("anyOf", "oneOf", "not"):
                # The default message dumps the whole value; say what is expected.
                hint = err.schema.get("x-hint", "does not match any allowed form")
                msg = f"{where}: {hint}"
            elif err.validator == "type" and isinstance(err.instance, dict) and "string" in _types(err.validator_value):
                # YAML reads `- text: more text` as a mapping, not as a text with a colon.
                text = "; ".join(f"{k}: {v}" for k, v in err.instance.items())
                msg = (f"{where}: should be text, but YAML read {text!r} as a key and a value because of the colon and space – "
                       f"put the item in quotes (\"{text}\") or replace the colon with a dash")
            else:
                msg = f"{where}: {err.message}"
            (warnings if err.validator == VOCAB_KEYWORD else errors).append(msg)
        return sorted(set(errors)), sorted(set(warnings))



def _types(value) -> list:
    return value if isinstance(value, list) else [value]
