<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/proavus-logo-dark.svg">
    <img src="brand/proavus-logo.svg" alt="Proavus" width="360">
  </picture>
</p>

<p align="center"><b>English</b> · <a href="README.cs.md">Čeština</a></p>

**Proavus** – evidence-first genealogy with AI: a method, a data schema and
tools for researching your family history with an LLM under the
Genealogical Proof Standard.

> **Work in progress (0.2.0).** The schema, the validator, the binding rules
> and the first commands (`/proavus:init`, `/start`, `/end`) exist; the guided
> setup (`/setup`) does not yet. Not ready for general use.

## How it will work

1. Create a GitHub account and install the Claude desktop app.
2. Ask Claude to set up Proavus – it installs everything and creates your
   own **private** family repository. Never put family data in a fork of
   Proavus: forks are public.
3. Open your private repository and type `/start`.
4. Describe who you are looking for; Claude helps you frame the question,
   plan the search and read the records.
5. Type `/end`: findings are saved with source citations and checked.

## What is here

| Part | Where |
|---|---|
| Ten binding rules | [method/rules.md](method/rules.md) |
| Reading records | [method/reading-records.md](method/reading-records.md) |
| Data schema v0 | [schema/](schema/README.md) |
| Validator | `uv run tools/validate.py <family-repo>` |
| Family map | `uv run tools/build_views.py <family-repo>` → `views/mapa.html` |
| Architecture and decisions | [docs/architecture.md](docs/architecture.md) (Czech for now), [docs/decisions/](docs/decisions/) |

## Licence

| Part | Licence |
|---|---|
| Method and documentation (`method/`, `docs/`, `regions/`, README) | CC BY 4.0 |
| Code (`tools/`, `tests/`, hooks, workflows) | MIT |
| Schema, vocabularies, family repository template | CC0 1.0 |
| Name and logo (`brand/`) | all rights reserved |

Details in [`REUSE.toml`](REUSE.toml) and [`LICENSES/`](LICENSES/).
© 2026 Petr Bělohlávek and Proavus contributors.
