# Changelog

One version for the whole repository: method, schema, tools and plugin
(ADR 0018). Format: added = minor, fix = patch, breaking schema change =
major + `migrate.py`.

## 0.3.0 – unreleased

- From the identity gate of a family repository (fictional examples):
  participant roles `spouse-father`, `spouse-mother`, `grandfather`,
  `grandmother` (ADR 0044, also in the sex check); EDTF with single
  unspecified digits in month and day – `1855-02-1X`, `1855-1X`,
  `1855-02-X5` – only real dates, shown as „10.–19. 2. 1855“ (ADR 0045,
  `edtf.expand`); `participant.marital_status_as_written` and
  `marital_status` (vocabulary `marital_statuses`: single, married, widowed,
  divorced) next to `status_as_written` (ADR 0046) – `upgrade-plan` lists
  participants whose `status_as_written` holds a marital status, the method
  (§4) says how to split them. Existing data stay valid unchanged.
- Workflows (ADR 0043): `actions/checkout` and `astral-sh/setup-uv` pinned to
  a commit SHA (v4.4.0, v6.8.0) in the framework CI and the family
  template; `permissions: {}` for the workflow, `contents: read` for the
  job; `persist-credentials: false`; Dependabot for GitHub Actions in the
  framework (weekly, 7-day cooldown). Families get the new pins with
  `/proavus:upgrade`. `tests/test_workflows.py` keeps it that way.
- Bringing older research in (ADR 0042, `docs/import.md` + Czech): plan
  files with symbolic keys and `@key` links (header, sentences, body), new
  IDs, files in the hand-written style and the right folders
  (`proavuslib/bulk.py`, `tools/bulk_import.py --dry-run`, copied into
  `.proavus/`); the whole batch is written only if it validates, no file
  exists and every entry of the old diary is linked (`diary:` /
  `from_diary:`, the original text quoted in the body); keys kept in
  `archive/import-keys.yaml` for later plans. Order: archive → pilot
  question → the rest → daily sessions from the diary → check the diary
  links. Fictional example in `examples/import/`.
- `tools/archive_fetch.py` (ADR 0041): ARON – `book` (metadata), `list`
  (images and sizes, downloads nothing), `link`, `get --dry-run` / `get`
  (only into a folder outside any repository, at most `--max` images per
  call, default 10, limit 50, a pause between images, checks content type,
  size and a complete JPEG). Acta Publica and Matricula Online: `link` only –
  their terms of use / robots.txt do not allow automated access; nothing is
  fetched from them. Standard library only; copied into `.proavus/`.
- `/proavus:start` and the family `AGENTS.md`: images only after the user's
  explicit yes to the list from `get --dry-run`.
- Method (`reading-records.md`) and new `regions/cz/pitfalls.md`: index
  numbers are often pages, two anchors for page → image, crops with ~10 %
  margin, whole-book ZIPs in lower resolution, `P`/`Š`/`Ř`/`R`, margin notes
  are later, age column above 30 is years, married women under the husband's
  name, the parents' marriage also in the next book, cemetery maps incomplete
  and a grave proves no parenthood.
- START-HERE (ADR 0039): name, question title, record in words, conflict
  and inquiry labels next to every ID (`proavuslib/labels.py`); a summary
  per open question (who, searches and results, records, last next step,
  conflicts, inquiries, open tasks, planned sources) instead of a table;
  open human tasks with a state from all sessions, plain-text tasks only
  from the latest session (also in the map); the first ten warnings.
- Validator (ADR 0040): negatives from an index only in one grouped warning,
  and `coverage.index_negative_accepted: {by, on, note}` to accept one;
  the participant's sex (stated or from the role) must fit the person of an
  identity link (error for probable / proved, warning below); possible
  duplicate persons (same name without diacritics, overlapping birth) with
  `person.distinct_from` for known namesakes; the same fact twice (type,
  date, value); advice what to add for `vital_status: unknown`.
- `proavuslib/dates.py` (dates in words, moved from `build_views.py`).
- **Schema 0.3** (core, additive – old forms stay valid; ADR 0031–0038):
  `record.crops` (path + caption; `crop` stays as the short form);
  `record.annotations` (later notes in the margin: text, position, hand,
  when written, the event and its date); `reading.read_by` = members who
  read it, `reading.read_by_agent` = AI reading – a confirmed reading needs
  a member in `read_by` who confirmed it, and only such a reading passes the
  identity gate; `oral.speakers` (`speaker` stays for one); coverage ranges
  as a `query` for database searches; new entity `inquiry` (`IN-…`,
  `inquiries/`: addressee, sent, state sent / acknowledged / answered /
  closed, result, records) and `session.inquiries`; human tasks
  `{task, status: open / done / dropped, for, by, on}`; `relationship.citations`
  (also in the identity gate).
- START-HERE and the map show only open human tasks (from all sessions) and
  inquiries not closed.
- `migrate.py` runs migrations by the version that brought them (ADR 0030):
  required for a major version, allowed for a minor one to rewrite data into
  the new form. 0.3.0: `crop` → `crops`, human tasks as text → open tasks.
  `proavuslib.frontmatter.join` writes headers back in the hand-written
  style (short lists `[a, b]`, indented items, plain dates), so a migration
  changes only the lines it converts.
- Method and skills: who read a record (person or agent), margin notes,
  inquiries, closing human tasks.
- Fictional fixture: two crops and a margin note, an agent reading, an
  inquiry, a database search, oral testimony with two speakers, a
  relationship with direct citations, open and done human tasks.
- Family map (ADR 0029): dates in the map's language and EDTF in words
  (cs `13. 5. 1958`, `kolem 1868`, `před 26. 1. 1836`, `1946/1947`);
  `map.lang` defaults to the region's language (`cz` → `cs`); of several
  facts of one type the card shows the strongest (information, evidence,
  confidence) and marks **≠** a disagreeing or equally strong other
  version, all versions in the detail; names and record titles instead of
  IDs in conflicts, questions and citations; long occupations and places
  shortened on the card; `map.living_places` (birth place of living
  persons, default false – then also no source title in their citations);
  `--hide-living` writes `views/mapa-sdileni.html` for sharing outside the
  family. Screenshots in `docs/images/` updated.
- Fictional fixture: a second, equally strong birth of Matěj (part of the
  open conflict) and his long occupation.
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
