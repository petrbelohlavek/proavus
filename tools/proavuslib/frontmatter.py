"""Read Markdown files with a YAML header (front matter)."""

from __future__ import annotations

import re

import yaml


class _Loader(yaml.SafeLoader):
    """SafeLoader with YAML 1.2-like scalars.

    Dates stay strings (EDTF and ISO dates are text), and only true/false are
    booleans – in YAML 1.1 the keys `on`, `no`, `yes` would become booleans.
    """


_DROP = {"tag:yaml.org,2002:timestamp", "tag:yaml.org,2002:bool"}
_Loader.yaml_implicit_resolvers = {
    key: [(tag, rx) for tag, rx in resolvers if tag not in _DROP]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def load_yaml(text: str):
    return yaml.load(text, Loader=_Loader)


def split(text: str) -> tuple[dict, str]:
    """Return (header, body). Raises ValueError if the header is missing or broken."""
    text = text.lstrip("﻿")
    if not text.startswith("---\n") and not text.startswith("---\r\n"):
        raise ValueError("missing YAML header (file must start with ---)")
    lines = text.splitlines(keepends=True)
    for i in range(1, len(lines)):
        if lines[i].rstrip("\r\n") == "---":
            header = "".join(lines[1:i])
            body = "".join(lines[i + 1:])
            break
    else:
        raise ValueError("YAML header is not closed with ---")
    try:
        data = load_yaml(header)
    except yaml.YAMLError as exc:
        raise ValueError(f"YAML header cannot be read: {exc}") from None
    if not isinstance(data, dict):
        raise ValueError("YAML header must be a mapping (key: value)")
    return data, body


class _Dumper(yaml.SafeDumper):
    """SafeDumper that writes YAML the way people write the headers by hand:
    dates and `on`/`no` plain, short lists of scalars as [a, b], list items
    indented under their key, double quotes only where needed."""

    def increase_indent(self, flow=False, indentless=False):
        return super().increase_indent(flow, False)


_Dumper.yaml_implicit_resolvers = {
    key: [(tag, rx) for tag, rx in resolvers if tag not in _DROP]
    for key, resolvers in yaml.SafeDumper.yaml_implicit_resolvers.items()
}
_Dumper.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def _represent_str(dumper, value):
    plain_ok = dumper.resolve(yaml.ScalarNode, value, (True, False)) == "tag:yaml.org,2002:str"
    special = value != value.strip() or value == "" or any(c in value for c in ":#[]{},&*!|>'\"%@`") and not _safe_plain(value)
    style = None if plain_ok and not special else '"'
    return dumper.represent_scalar("tag:yaml.org,2002:str", value, style=style)


def _safe_plain(value: str) -> bool:
    """Characters that need quotes only in some positions: allow them inside ordinary text."""
    return not (value[0] in "-?:,[]{}#&*!|>'\"%@`" or ": " in value or " #" in value or value.endswith(":"))


def _represent_list(dumper, items):
    flow = len(items) <= 6 and all(isinstance(i, (str, int)) and not isinstance(i, bool) for i in items) \
        and sum(len(str(i)) for i in items) < 60 and all(_safe_plain(str(i)) and not any(c in str(i) for c in ", ") for i in items if str(i))
    return dumper.represent_sequence("tag:yaml.org,2002:seq", items, flow_style=flow)


_Dumper.add_representer(str, _represent_str)
_Dumper.add_representer(list, _represent_list)


def join(data: dict, body: str) -> str:
    """Inverse of split(): a Markdown file with a YAML header."""
    header = yaml.dump(data, Dumper=_Dumper, allow_unicode=True, sort_keys=False, width=1000)
    return f"---\n{header}---\n{body}"
