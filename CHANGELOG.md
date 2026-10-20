# Changelog

One version for the whole repository: method, schema, tools and plugin
(ADR 0018). Format: added = minor, fix = patch, breaking schema change =
major + `migrate.py`.

## 0.3.0 – unreleased

- Plugin skill `/proavus:upgrade` and its deterministic part in
  `family_repo.py` (ADR 0009, 0014, 0018): `upgrade-plan` compares
  `.proavus/VERSION` with the plugin and shows the CHANGELOG sections in
  between, schema changes (new and removed fields and vocabulary values),
  whether a migration is needed and missing map settings with candidate
  starting persons; `upgrade` reinstalls `.proavus/`, refreshes the
  `proavus:begin/end` blocks and the check workflow (never the family's own
  text), migrates data on a major version change, sets `schema_version` and
  `map.root` / `map.lang`, validates with the new copy and prints the commit
  message. Never downgrades.
- `tools/migrate.py`: skeleton with a registry of migrations between major
  versions (none yet); refuses a major upgrade whose migration is missing.
  Copied into `.proavus/` with the other tools.
- `START-HERE.md`: when the repository's copy is newer than the plugin it now
  says to update the plugin instead of suggesting an upgrade.
- References to `/proavus:upgrade` corrected in the family template
  (`AGENTS.md` block, README, `repo.yaml`), `.proavus/README.md` and
  `/proavus:start`: what it changes, when and where to run it.
- Tested on a fictional repository as left by 0.1.0 (0.1.0 → 0.2.0 plan and
  upgrade to the plugin version, including the map settings).
- How to use `/proavus:init`, `/proavus:start` and `/proavus:end` – what
  each does, where to type it (the folder of the session) and what to do
  if you forget one: in the family repository template README (for family
  members) and in README (EN, CS).
- Commands always with their full plugin names (`/proavus:start`,
  `/proavus:end`) in README, the template and the skills.

## 0.2.0 – 2026-10-20

First release (`stable`); includes everything listed under 0.1.0.

- README (EN, CS): installing the plugin from the local catalogue
  (`.claude-plugin/marketplace.json`) in Claude Code desktop and CLI, step by
  step, with checks that `/proavus:init`, `/proavus:start` and
  `/proavus:end` are available; update and removal.
- `/proavus:init` and `family_repo.py init` accept an existing empty
  repository that contains `.claude/` besides `.git` (Claude Code creates it
  when the folder is opened).
- `family_repo.py protect-plugin` and a new `/proavus:init` step: the family
  repository's `.claude/settings.local.json` denies Claude Code's
  file-editing tools in the plugin folder (`Edit(//<folder>/**)` – one Edit
  rule covers Write too); the skill explains that shell commands are not
  covered and rely on the agent following `AGENTS.md`.
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
- Family map layout (ADR 0028): generation columns with cards coloured by
  how well the person is documented (best QUAY), open-conflict mark,
  marriage label on the lines, person detail in a dialog, boxes with open
  conflicts, questions, next steps and persons outside the tree.
- Czech map labels for statuses, evidence and locator parts; plural forms in
  the counts.
- README (EN, CS): screenshots of the map on the fictional family
  (`docs/images/`, how to make them again in `docs/images/README.md`).
- `family_repo.py install-tools` and `build_views.py` refuse the framework
  itself and folders without `repo.yaml` (`.proavus/` was installed into the
  framework by mistake).
- `/start` tells how to build the family map on request.
- Name guard: names inside identifiers (`name_line`, `name2`, `nameFamily`)
  are now hits; underscores, digits and camelCase no longer hide them.
- Fictional fixture extended (seven persons over five generations, step and
  unknown parent, living persons, open conflict).

## 0.1.0 – not released separately (part of 0.2.0)

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
