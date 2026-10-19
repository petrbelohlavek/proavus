# 0018 Jedna sémantická verze pro celé repo

- **Stav:** přijato (2026-10-20)
- **Původně:** R23

## Kontext

Plugin, metodika, schéma a nástroje se vydávají společně (ADR 0014); oddělené verze by nikdo neudržel.

## Rozhodnutí

Jedna verze (`version` v `plugin.json`), začíná 0.1.0. Přidání = menší verze, oprava = poslední číslo, zásadní změna schématu = hlavní verze + `migrate.py`. Každé vydání = posun větve `stable` + záznam v `CHANGELOG.md`. Rodinné repo uvádí verzi schématu v `repo.yaml` a `.proavus/`.

## Důsledky

Verze v `pyproject.toml` a `proavuslib.SCHEMA_VERSION` se posouvají spolu s `plugin.json`.
