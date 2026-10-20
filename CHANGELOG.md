# Changelog

One version for the whole repository: method, schema, tools and plugin
(ADR 0018). Format: added = minor, fix = patch, breaking schema change =
major + `migrate.py`.

## 0.2.0 – unreleased

- `tools/build_views.py`: family map `views/mapa.html` – one self-contained
  HTML file without CDN (ADR 0027). Ancestor tree of the starting person,
  lines by relationship confidence (proved / probable / possible / not
  proved), non-biological and unknown parents; person cards with names,
  facts with confidence and sources, relationships, open conflicts and
  questions. Living persons only as rule 9 allows. Copied into `.proavus/`
  by `family_repo.py install-tools`.
- Schema: `map` in `repo.yaml` now has defined fields `root` (starting
  person) and `lang` (`en`, `cs`); the validator checks that `map.root` is
  a person.
- `family_repo.py install-tools` and `build_views.py` refuse the framework
  itself and folders without `repo.yaml` (`.proavus/` was installed into the
  framework by mistake).
- `/start` tells how to build the family map on request.
- Name guard: names inside identifiers (`name_line`, `name2`, `nameFamily`)
  are now hits; underscores, digits and camelCase no longer hide them.
- Fictional fixture extended (seven persons over five generations, step and
  unknown parent, living persons, open conflict).

## 0.1.0 – unreleased

First minimal framework (build step 2).

- Repository skeleton; family-name guard hooks (`.githooks/`, `tools/guard_names.py`).
- Licences by part with REUSE (CC BY 4.0, MIT, CC0 1.0, brand reserved).
- Brand files (logo, icon, favicon, social preview).
- Plugin manifest: the whole repository is the plugin (`source: "."`).
- Data schema v0: 13 entities (8 full, 5 minimal), record participants,
  identity assertions, 11 vocabularies, regional extension `cz`.
- `tools/validate.py` (schema, IDs, links, identity gate, living persons,
  impossible dates, negative searches, sessions) and `tools/new_id.py`, with
  tests on fictional data; CI with tests and REUSE lint.
- Method: `method/rules.md` (+ Czech), `method/reading-records.md`.
- Documentation: `docs/architecture.md` and 26 ADRs in `docs/decisions/`.
- Family repository template `templates/family/` and `tools/family_repo.py`
  (init, install of the pinned copy `.proavus/`, START-HERE, privacy check).
- Plugin skills `/proavus:init` (the bare `/init` is a built-in Claude Code
  command), `/start` and `/end`.
