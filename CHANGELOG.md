# Changelog

One version for the whole repository: method, schema, tools and plugin
(ADR 0018). Format: added = minor, fix = patch, breaking schema change =
major + `migrate.py`.

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
