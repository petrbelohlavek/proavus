# Proavus data schema v0

JSON Schema (draft 2020-12) for the YAML header of every file in a family
repository. One entity = one Markdown file named after its ID
(`<ID>.md` or `<ID>--<slug>.md`). Checked by `tools/validate.py`.

| Entity | Directory | ID prefix | Status in v0 |
|---|---|---|---|
| `question` | `questions/` | `Q` | full |
| `session` | `sessions/YYYY/` | `S` | full |
| `coverage` | `coverage/` | `C` | full |
| `record` (with participants) | `records/` | `R` | full |
| `source` | `sources/` | `SO` | full |
| `person` | `people/` | `P` | full |
| `relationship` | `relationships/` | `RL` | full |
| `assertion` (fact / identity) | `assertions/` | `A` | full |
| `conflict` | `conflicts/` | `X` | minimal |
| `place` | `places/` | `PL` | minimal |
| `oral` | `oral/` | `O` | minimal |
| `decision` | `decisions/` | `D` | minimal |
| `chronicle` | `chronicle/` | `CH` | minimal |
| `inquiry` | `inquiries/` | `IN` | full (0.3, ADR 0036) |

Plus `repo.schema.json` for `repo.yaml` and shared definitions in
`common.schema.json`.

## Four layers of extensibility (ADR 0015)

1. **Core** – entities, IDs, links, assertions, record participants,
   confidence, locator. Changes rarely; a breaking change = major version +
   `migrate.py`.
2. **Vocabularies** – `vocab/*.yaml` (event and fact types, name types,
   participant roles, relationship types and subtypes, religions, source kinds,
   search methods, place types, milestone types). Fields marked `x-vocab` in
   the schema. An unknown value is only a warning; adding a value is a minor
   version.
3. **Regional extensions** – `regions/<code>/schema-ext.yaml`, switched on by
   `extensions:` in `repo.yaml` (e.g. `cz`: house number, estate).
4. **Safety net** – `schema_gap:` notes on any entity for what the schema
   cannot express yet; research never stops because of the schema.

## Key rules

- **Participants are not persons** (ADR 0017): a record lists people exactly
  as written; linking participant `p2` of a record to a person is an
  `assertion` of kind `identity`.
- **Facts are assertions**, not person fields (ADR 0015).
- **Two axes** (ADR 0022): the source has a *form* (original / derivative /
  authored); each citation has *information* (primary / secondary /
  undetermined) and *evidence* (direct / indirect / negative); the conclusion
  has a *confidence* (proved / probable / possible / not-proved / disproved).
  GEDCOM QUAY is derived from them, never entered.
- **Identity gate** (ADR 0016): a record read only once (`read-once`) may not
  support `proved`, a probable or proved identity link, or a merge; these need
  `confirmed` (by, on) – a human decision in the session.
- **Dates** are an EDTF subset: `1935`, `1935-04-12`, `1935?`, `1935~`,
  `19XX`, `1904/1906`, `../1900`.
- **Readings** (ADR 0033): `read_by` lists the members (humans) who read a
  record from the image, `read_by_agent` an AI reading; only a member in
  `read_by` may confirm it, and only a confirmed reading passes the identity
  gate.

## New in 0.3

- `record.crops` (path + caption; `crop` stays as the short form) and
  `record.annotations` – later notes in the margin (ADR 0031, 0032);
- `oral.speakers` (`speaker` stays for one, ADR 0034);
- coverage ranges given as a `query` for database searches (ADR 0035);
- entity `inquiry` – requests to offices with a state (ADR 0036);
- human tasks with a state `open` / `done` / `dropped` (ADR 0037);
- `relationship.citations` (ADR 0038);
- `coverage.index_negative_accepted: {by, on, note}` and `person.distinct_from`
  – decisions about warnings of the validator (ADR 0040).

Old forms stay valid; `/proavus:upgrade` rewrites them with the 0.3.0
migration (`tools/migrate.py`, ADR 0030).

Unknown fields are errors (typos are caught); unknown vocabulary values are
warnings.
