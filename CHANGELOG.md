# Changelog

One version for the whole repository: method, schema, tools and plugin
(ADR 0018). Format: added = minor, fix = patch, breaking schema change =
major + `migrate.py`.

Every version has a git tag `vX.Y.Z` and a GitHub release, older ones
added on 2026-10-21. `v0.1.0` and `v0.2.1` mark versions that were not
released on `stable` (their changes are in 0.2.0 and 0.3.0).

## 0.5.0 – unreleased

- `/proavus:setup` – a guide for a family member without technical
  knowledge: checks and installs git, gh and uv (macOS, Windows), logs in to
  GitHub in the browser, recommends two-factor login, installs the plugin
  from the catalogue, clones the private family repository, adds the member
  to `repo.yaml` (abbreviation, role) with a commit or a pull request
  according to their access, and hands over to `/proavus:start`. Every step
  is skipped when already done. Never passwords or tokens in the chat
  (ADR 0048).
- `family_repo.py access <folder|owner/name>`: private? save directly
  (admin, maintain), through a pull request (write) or read only; not found
  or no access yet.
- `family_repo.py add-member`: adds a member to `repo.yaml` and keeps the
  rest of the file as written; refuses a taken abbreviation.
- `/proavus:start`: a member missing in `repo.yaml` – first looks for an open
  pull request `member-<abbr>`, otherwise adds them with `add-member`.

## 0.4.0 – 2026-10-21

- Schema (core, additive): a human task may name the `question` it serves,
  and a `conflict` or an `inquiry` (ADR 0047).
- START-HERE shows each open task once: under the open question it serves;
  tasks without one (or for a question no longer open, with its state) in
  their own block. The last session of a question is only a session that
  worked on it – its only question, or a search, record, inquiry or task of
  that question.
- Validator: warning for an open task of an answered, bounded or abandoned
  question; advice to write an `inquiry` when an open task names an e-mail
  address or the words odpověď / dotaz / žádost.
- `migrate.py` 0.4.0: fills in `question` where it is unambiguous (the task's
  inquiry is about one question, or the session has only one).
- `/proavus:end` and `method/reading-records.md`: tasks with their question.

## 0.3.1 – 2026-10-21

- README (EN, CS), installing and updating the plugin: clone and keep the
  framework folder on the `stable` branch – Claude Code installs whatever is
  checked out there; check the installed version and commit in
  `~/.claude/plugins/installed_plugins.json` (one command) – `claude plugin
  list` / `details` read the folder, not the installed copy; update by
  `git pull`, `marketplace update`, `uninstall` and `install` –
  `claude plugin update` alone installs only a new version number; the
  session check now lists four commands including `/proavus:upgrade`.
- The same update steps in `/proavus:upgrade` (exit 3) and in START-HERE
  when the plugin is older than the repository.

## 0.3.0 – 2026-10-21

**Upgrading from 0.2.0:** update the plugin (`claude plugin marketplace
update proavus`, `claude plugin update proavus@proavus`), open a new session
in the family repository and run `/proavus:upgrade`. It rewrites `crop` into
`crops` and plain-text human tasks into open tasks (the old forms stay
valid), asks for the map's starting person and language, and lists
participants whose `status_as_written` holds a marital status. If an agent
did the first reading of a record but a member is in `read_by`, add
`read_by_agent` – no migration can tell.

### Schema 0.3 (core and vocabularies, additive – existing data stay valid)

- `record.crops` (path + caption; `crop` stays as the short form) and
  `record.annotations` – later notes in the margin: text, position, hand,
  when written, the event and its date (ADR 0031, 0032).
- Readings by people and by an agent: `reading.read_by` = members who read
  the entry, `reading.read_by_agent` = AI reading; a reading is confirmed
  only by a member in `read_by`, and only such a reading passes the identity
  gate (ADR 0033).
- `oral.speakers` (`speaker` stays for one) (ADR 0034); coverage ranges as a
  `query` for database searches (ADR 0035).
- New entity `inquiry` (`IN-…`, `inquiries/`): requests to offices,
  archives and parishes with state sent / acknowledged / answered / closed,
  result and records; `session.inquiries` (ADR 0036).
- Human tasks `{task, status: open / done / dropped, for, by, on}` (ADR 0037).
- `relationship.citations`, also in the identity gate (ADR 0038).
- `coverage.index_negative_accepted: {by, on, note}` and
  `person.distinct_from` (ADR 0040).
- Participant roles `spouse-father`, `spouse-mother`, `grandfather`,
  `grandmother` (ADR 0044); `marital_status_as_written` and
  `marital_status` (vocabulary `marital_statuses`) next to
  `status_as_written` (ADR 0046).
- EDTF: single unspecified digits in month and day of a known year –
  `1855-02-1X`, `1855-1X`, `1855-02-X5`; only dates that can exist
  (ADR 0045, `edtf.expand`).
- `repo.yaml`: `map.living_places` (ADR 0029).

### Validator

- Negatives from an index only in one grouped warning, acceptable with
  `index_negative_accepted`; the participant's sex (stated or from the role)
  must fit the person of an identity link – error for probable / proved,
  warning below; possible duplicate persons (same name without diacritics,
  overlapping birth); the same fact twice (type, date, value); advice what to
  add for `vital_status: unknown` (ADR 0040).
- Query-only ranges only for database searches; inquiry dates in order and
  not in the future; a crop or crops, not both; every crop must exist.

### Tools

- `/proavus:upgrade` and `family_repo.py upgrade-plan` / `upgrade`
  (ADR 0009, 0014, 0018): shows the CHANGELOG sections in between, schema
  changes, migrations, missing map settings with candidate starting persons
  and participants whose `status_as_written` holds a marital status;
  reinstalls `.proavus/`, refreshes the `proavus:begin/end` blocks and the
  check workflow (never the family's own text), runs migrations, sets
  `schema_version` and `map`, validates with the new copy, prints the commit
  message; never downgrades.
- `tools/migrate.py` (ADR 0030): migrations by the version that brought
  them – required for a major version, allowed for a minor one to rewrite
  data into the new form; 0.3.0: `crop` → `crops`, plain-text human tasks →
  open tasks. `proavuslib.frontmatter.join` writes headers back in the
  hand-written style, so a migration changes only the lines it converts.
- `tools/bulk_import.py` and `proavuslib/bulk.py` (ADR 0042,
  `docs/import.md` + Czech): bring older research in from a plan with
  symbolic keys and `@key` links; the whole batch is written only if it
  validates, no file exists and every entry of the old diary is linked
  (original text quoted); keys in `archive/import-keys.yaml`. Fictional
  example in `examples/import/`.
- `tools/archive_fetch.py` (ADR 0041): ARON – `book`, `list` (downloads
  nothing), `link`, `get --dry-run` / `get` into a folder outside any
  repository, at most `--max` images per call, content type, size and JPEG
  checks. Acta Publica and Matricula Online: `link` only – their terms of
  use / robots.txt do not allow automated access.
- All new tools are copied into `.proavus/`.

### Family map (ADR 0028, 0029)

- Layout of the pilot map: header with counts and legend, generation
  columns, cards coloured by how well the person is documented (best QUAY),
  open-conflict mark, marriage label on the lines, detail in a dialog, boxes
  with open conflicts, questions, next steps and persons outside the tree.
- Dates in words in the map's language; `map.lang` defaults to the region's
  language (`cz` → `cs`); the strongest of several facts of one type on the
  card, **≠** for a disagreeing or equally strong version; names and record
  titles instead of IDs; long occupations and places shortened.
- Living persons: birth place only with `map.living_places: true` (then
  also the source title in their citations); `--hide-living` writes
  `views/mapa-sdileni.html` for sharing outside the family.
- Screenshots of the fictional family in README (`docs/images/`).

### START-HERE (ADR 0039)

- A name, question title or record in words next to every ID; a summary per
  open question; open human tasks with a state from all sessions,
  plain-text tasks only from the latest session (also in the map);
  inquiries not closed; the first ten warnings; when the repository's copy
  is newer than the plugin it says to update the plugin.

### Method, skills, documentation

- `method/reading-records.md` and new `regions/cz/pitfalls.md`: who read a
  record (person or agent), margin notes, roles and marital status of
  participants, index numbers as pages, two anchors for page → image, crops
  with ~10 % margin, whole-book ZIPs in lower resolution, `P`/`Š`/`Ř`/`R`,
  age column above 30 is years, married women under the husband's name, the
  parents' marriage also in the next book, cemetery maps incomplete and a
  grave proves no parenthood.
- `/proavus:start`: images only after the user's yes to the dry-run list;
  older research via `docs/import.md`; inquiries; the family map with
  `--hide-living` for sharing. `/proavus:end`: closing human tasks,
  decisions that end warnings.
- How to use `/proavus:init`, `/proavus:start`, `/proavus:end` and
  `/proavus:upgrade` – what, where, if you forget – in the family template
  README and in README (EN, CS); full plugin command names everywhere.

### Security and CI (ADR 0043)

- `actions/checkout` and `astral-sh/setup-uv` pinned to commit SHAs in the
  framework CI and the family template – v7.0.1 and v10.3.0 (Dependabot
  raised them from v4.4.0 and v6.8.0; the release notes have no breaking
  change that applies: Node 24 on GitHub runners, no removed inputs used);
  `permissions: {}` for the workflow, `contents: read` for the job,
  `persist-credentials: false`; Dependabot for GitHub Actions in the
  framework (weekly, 7-day cooldown). `tests/test_workflows.py` checks pins,
  template parity and permissions.
- The name guard finds names inside identifiers (underscores, digits,
  camelCase).

### Tests and fixture

- 256 tests. Fictional fixture extended: two crops and a margin note, an
  agent reading, an inquiry, a database search, oral testimony with two
  speakers, a relationship with direct citations, open and done human tasks,
  a second birth of Matěj in the open conflict, a long occupation. Upgrades
  tested on repositories made by the real 0.1.0 and 0.2.0 code.

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
