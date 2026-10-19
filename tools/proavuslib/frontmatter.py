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
