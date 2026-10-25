# Changelog

One version for the whole repository: method, schema, tools and plugin
(ADR 0018). Format: added = minor, fix = patch, breaking schema change =
major + `migrate.py`.

Every version has a git tag `vX.Y.Z` and a GitHub release, older ones
added on 2026-10-21. `v0.1.0` and `v0.2.1` mark versions that were not
released on `stable` (their changes are in 0.2.0 and 0.3.0).

## Unreleased

- `archive_fetch.py` reads the source (ADR 0065): `book`, `list`, `link`
  and `get` take `--source SO-ID` (with `--repo` and `--volume`) instead of
  a URL – the book URL comes from the volume or the source – and refuse,
  without contacting the portal, what the source's `access.mode` does not
  allow (book, list and get need automated; link needs link or automated).
  A source never widens what its portal allows. The `start` and
  `registers` skills use `--source`.

## 0.7.1 – 2026-10-25

- Evals: two new tasks on the fictional family. `volume-out-of-order` – a
  marriage entered later in volume II, with only a note in volume I; the
  record names the volume in `locator.volume`, coverage names both volumes
  (ADR 0058). `image-numbering-break` – an unnumbered sheet after page 60
  shifts the images; the record names the image the page is really on and
  the image map gets a true anchor after the break, never a computed one
  (ADR 0061). Each with a grader, a reference solution and two wrong ones.
- Evals run on 0.7.0 with Claude Code and the framework tools allowed
  (results in `evals/README.md`): 5/5 for `data-not-instructions`,
  `index-is-not-the-record` and `volume-out-of-order`, 3/5 for `namesakes`
  (entry of the namesake not recorded, never linked), 1/5 for
  `image-numbering-break` (no anchor added after the break).
- Family `AGENTS.md` block: page → image from the anchors in the source's
  `image_map` with `locate.py`; when an image shows another page, read it
  and add an anchor – never a computed one. With it `image-numbering-break`
  passed 5/5. Reaches family repositories through `/proavus:upgrade`.
- Family `AGENTS.md` block: on a page you read, record every entry of the
  family surname, not only the one you looked for; a namesake gets his own
  record and stays unlinked until evidence decides. With it `namesakes`
  passed 5/5 (before 3/5). Reaches family repositories through
  `/proavus:upgrade`.

## 0.7.0 – 2026-10-24

- Volume of a source (ADR 0058): `record.locator.volume`,
  `coverage.ranges[].volume` and `source.volumes` (volumes in the archive's
  order, with period, call number, URL and note – periods may overlap). The
  validator checks that a record's or a range's volume is one the source
  lists, and warns about a record without a volume in a source that has
  them. A volume alone does not locate an entry. `upgrade-plan` lists
  records whose `page` seems to hold a volume (roman numeral, tom, Bd, sv.);
  move it with the user. The map shows the volume in citations.
- Map: an other version of a birth or death names where it comes from –
  the assertion, its record or source, the locator and the evaluation of its
  strongest citation (the source title only where the person's sources are
  shown); with several other versions, the equally strong one is marked.
  A place ID in one assertion and the same name as written in the other is
  no longer shown as another version.
- Second reading defined (ADR 0059): a person reads the decisive items
  again from the crop, after and apart from the first reading – after the
  agent and blind to its reading (`member-after-agent`), the same member on
  a later day (`member-later`, with the new `reading.read_on`), or another
  member (`second-member`). The reading's `confirmed` takes `basis`,
  `checked` (the items read) and `from` (crop or image). The validator
  checks that the basis fits `read_by`, `read_by_agent` and `read_on` and
  warns about a confirmation without basis; `upgrade-plan` lists them.
  Rule 5, `reading-records.md` §5, the `AGENTS.md` block and `/proavus:start`
  and `/proavus:end` describe the blind second reading.
- Index pointers (ADR 0060): an index search's coverage lists what the
  index gives as `pointers` – the name as written, optional event and date
  as written, where it leads (`to: {source, volume, page, folio, entry,
  image}`) and `followed`, the coverage of the book search. A pointer is a
  lead, not a record. The validator allows pointers only from an index with
  a found or partial result, checks that `followed` searched the book the
  pointer leads to and warns when it missed its volume or page, and warns
  about an assertion citing an index search as anything but negative
  evidence. START-HERE lists pointers not followed yet.
- Page → image from anchors (ADR 0061): `source.image_map`, one map per
  volume, `unit` page or folio, at least two anchors `{page | folio, image,
  by, on}` read on the images. New `tools/locate.py <SO-ID> --page N
  [--volume V]` computes the image between two anchors when the step is
  regular (one or more images per page, or several pages per image), says
  when it is only an estimate or when the anchors disagree (a break: add an
  anchor), and prints the `archive_fetch.py link` command; it is copied into
  `.proavus/`. The validator rejects anchors that cannot all be true and
  warns when a record's image does not fit the map.
- `/proavus:registers` (ADR 0062): a skill for searching registers –
  name forms and the right book first, the index as pointers, book and
  volume, page → image with `locate.py` and anchors, column headers,
  neighbouring entries and margin notes, the record with a blind second
  reading, coverage of the book with `followed`, and negative results.
  Claude also uses it on its own when a question leads to a register;
  `/proavus:start` points to it.
- Merging duplicate assertions (ADR 0063): new `tools/merge_assertions.py`
  – `plan` shows which assertion stays, the joined citations and every file
  whose links change, and stops where the researcher must decide (another
  confidence, another evaluation of the same citation, a confirmation on
  the assertion that would go, another place); `apply` writes it after
  their yes, rewrites the links, deletes the merged files and validates.
  Copied into `.proavus/`. The validator's duplicate check now also
  compares the place: the same date in two places is reported as two
  versions to write into a conflict, not as a duplicate, and the advice to
  join citations names the command.
- Access and legal time limits (ADR 0064): `source.portal` (an id from the
  portal catalogue) and `source.access: {mode, held_by, note}` (automated,
  link, manual, on-site, request, none); the validator warns about an
  unknown portal and rejects a source that claims more than its portal
  allows. `regions/cz/access.yaml`: anyone may see a birth entry after 100,
  a marriage after 75 and a death after 30 years from the entry (zákon
  č. 301/2000 Sb.). `coverage.event` with the dates of the ranges gives the
  year all searched entries are open; a negative over a range not open yet
  is a warning, and START-HERE lists inaccessible searches with that year
  or says the limit has passed. New `tools/access.py limit|source`; both
  copied into `.proavus/`.

## 0.6.2 – 2026-10-23

- Docs: the README picture of the two kinds of repositories draws its
  words as outlines (Gelasio, DejaVu Sans Mono) from
  `docs/images/lettering.json`, made once by `docs/images/lettering.py`;
  it needs no font and looks the same everywhere (ADR 0057). A test checks
  it has no text and no font.

## 0.6.1 – 2026-10-22

- Fix: `eval.py run` shows the end of the agent's output when the agent
  fails (exit code other than 0, timeout) and counts the attempt as an agent
  error, not as the model's result; before, the output was dropped and the
  attempt looked like a model that did nothing.
- Evals: first run recorded (Claude Code, five attempts per task: 5/5, 4/5,
  5/5) in `evals/README.md`; ADR 0055 accepted.
- Method: an index and the book it points to are two searches and two
  coverage files; the record found goes into the book's `found`
  (`method/reading-records.md` §6, `/proavus:start`) – the one failure of
  the evals.

## 0.6.0 – 2026-10-22

- Public project files before publication (ADR 0054): `CONTRIBUTING.md`
  (no real family data anywhere, research-driven changes, hooks with the
  contributor's own guard list, tests, REUSE, licence of contributions),
  `CODE_OF_CONDUCT.md`, `SECURITY.md` (family data leaks count as security
  problems, private reporting only, fixes for `stable`) and issue forms
  *Bug* and *Research need* with a required confirmation that no real
  family data are included; blank issues off.
- Evals (ADR 0055, proposed): `evals/` with three tasks on the fictional
  family – `index-is-not-the-record`, `namesakes`, `data-not-instructions` –
  each with its question, archive pages as text in `portal/`, a grader and
  reference solutions; `tools/eval.py list|prepare|grade|run` runs any agent
  command in a fresh workspace and counts the passed attempts.
- Logo lettering as outlines (ADR 0056): the name and subtitle in
  `proavus-logo.svg`, `proavus-logo-dark.svg` and `proavus-social.svg` are
  drawn from the open font Gelasio (metric-compatible with Georgia) and need
  no font; `brand/lettering.py` redraws them; `proavus-social.png` exported
  again.
- Fix: the name guard (`tools/guard_names.py`) blocks commits when the guard
  list exists but has no entries (empty, or comments only), as it does when
  the list is missing. Before, such a list let every check pass and guarded
  nothing.

## 0.5.0 – 2026-10-21

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
- Family repository template: `.githooks/pre-commit` (Python, started by
  `uv`) validates exactly what is staged with `.proavus/tools/validate.py`
  and stops a commit with errors, with a message in Czech and English
  (ADR 0049).
- `family_repo.py hooks`: sets `core.hooksPath = .githooks` (per clone) and
  marks the hook executable, also in git for clones made on Windows.
  `/proavus:init`, `/proavus:setup`, `/proavus:start` and `/proavus:upgrade`
  switch it on; `upgrade` adds and refreshes the hook like the workflow.
- Skills validate before every commit (`/proavus:init`, the claim in
  `/proavus:start`, `/proavus:end` again after the pull, `/proavus:setup`,
  `/proavus:upgrade`) and never bypass the hook.
- Regional package `at` (Austria, Vienna; ADR 0050): `schema-ext.yaml`,
  `pitfalls.md` from the pilot (Matricula indexes and locators, two volumes a
  year, baptisms leading to the parents' marriage, abbreviated parishes, the
  wife's given name, margin notes, books blocked for 100 years and after
  cremation, Friedhöfe Wien, WStLA and Standesamt, ANNO and Lehmann) and
  `portals.yaml`. Switch it on with `regions` and `extensions: [at]` (also
  together with `cz`) in `repo.yaml`; `/proavus:init` offers it.
- Portal catalogue `regions/*/portals.yaml`: access (`automated`, `link`,
  `manual`), why, and notes from research for every portal;
  `archive_fetch.py portals [--region R]` lists it; a `manual` portal
  (Friedhöfe Wien, WStLA, ANNO, Lehmann, digi.ceskearchivy.cz) is refused
  with its address and notes, nothing is fetched. Copied into `.proavus/`;
  `archive_fetch.py` now needs PyYAML.
- `regions/cz/pitfalls.md`: guardianship files of illegitimate children at
  the district court of the domicile (today the State District Archive),
  separate index books of SOA Třeboň ("Kniha strana číslo"), SOA Zámrsk now
  SOA v Hradci Králové, archivní oddělení Zámrsk, Acta Publica behind
  Cloudflare (links only).
- Schema (regional, additive): `domicile_as_written` and `domicile_place`
  for a record participant in `cz` and `at`; event `church-exit` in `at`
  (ADR 0051). Two extensions may share a field only with the same
  definition – otherwise an extension error.
- Schema (core, additive): `coverage.searched_by` – `member` or `agent` (on
  the member's instruction), with `agent_model` (ADR 0052). `/proavus:start`
  and `/proavus:end` write it for every new search.
- Method: `reading-records.md` §4 – domicile right; a budget and a stop rule
  before following godparents, witnesses or neighbours into other books.
  `/proavus:start` reads the pitfalls of the repository's regions and checks
  the portal catalogue before using a portal.
- README for everyone (EN, CS) and `TECHNICAL.md` (English only) with
  everything technical; a language and audience switch on every page; a
  picture of the two kinds of repositories without words, generated by
  `docs/images/architecture.py` (ADR 0053). Links to "Update to a new
  release" now lead to `TECHNICAL.md`.

**Upgrading from 0.4.0:** `/proavus:upgrade` adds `.githooks/pre-commit` and
switches it on in that clone; other members get it switched on by their next
`/proavus:start`.

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
