# 0021 Nástroje smí mít připnuté závislosti (PyYAML, jsonschema)

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

ADR 0011 předpokládal jen standardní knihovnu Pythonu. Ta neumí YAML ani JSON Schema; vlastní parser by byl pracný a chybový právě v datech rodiny.

## Rozhodnutí

Nástroje deklarují připnuté závislosti v hlavičce PEP 723 (`pyyaml==6.0.2`, `jsonschema==4.23.0`); `uv run` je stáhne sám při prvním spuštění. Pro vývoj a testy jsou stejné verze v `pyproject.toml` (test hlídá shodu). Kontrola jmen (`guard_names.py`) a `new_id.py` zůstávají jen se standardní knihovnou.

## Důsledky

První spuštění potřebuje internet; potom běží z mezipaměti `uv`. Aktualizace závislostí = vědomá změna verze.
