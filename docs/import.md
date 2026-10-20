<!-- Czech: import.cs.md -->
# Bringing older research into Proavus

Most families start with something: a notebook of searches, notes in a word
processor, a tree drawn by an uncle, a genealogy program. This guide turns it
into Proavus files without writing your own scripts – Claude writes a **plan**
(one YAML file), `tools/bulk_import.py` checks it and creates the files.

A complete fictional example is in [`examples/import/`](../examples/import/):
the old notes (`old-notes.md`), the pilot plan (`01-pilot.yaml`) and the rest
(`02-rest.yaml`).

## The order that works

1. **Archive first.** Copy the old material unchanged into `archive/`
   (exports, scans of the notebook, the tree file). It stays frozen: the new
   files cite it, nobody edits it. Nothing gets lost even if the conversion
   is imperfect.
2. **A pilot question.** Pick one question the old notes almost answer
   (e.g. "When did Václav die?") and convert only what belongs to it: the
   sources, the records with their transcripts, the persons, assertions and
   relationships, the searches (`coverage`) and the sessions. Check the
   result together – `validate.py`, `START-HERE.md`, the family map. Adjust
   how you convert before doing more.
3. **The rest**, in batches of the same shape. A later plan links what an
   earlier one created (`@jan`), the keys are remembered.
4. **Daily sessions from the diary.** Every day of the old diary becomes a
   `session` (`sessions/YYYY/`, the date of the day searched) with what was
   searched (`coverage`), found (`records`) and the next step written then.
5. **Check that every diary entry has a link.** Each entry of the old diary is
   listed in the plan (`diary:`) and linked by at least one new file
   (`from_diary:`). The tool refuses to write while one is missing, and it
   quotes the original text in the body of the files that link it.

In a session: "Help me bring my old notes in, following
`${CLAUDE_PLUGIN_ROOT}/docs/import.md`." Claude reads the archive, proposes
the pilot plan, shows the dry run, and writes only after your yes.

## The plan

```yaml
member: ab                    # whose IDs (from repo.yaml)
diary:                        # entries of the old diary, each must be linked
  - ref: diary 1998-04-11
    text: Archiv Vzorkov, matrika N 1880–1890, str. 12 – křest Jana …
entities:
  - key: jan                  # symbolic key instead of an ID
    type: person
    slug: jan-ukazka          # optional: file name P-…--jan-ukazka.md
    names: [{value: Jan Ukázka, name_type: czech}]
    sex: male
    vital_status: deceased
  - key: bapt-jan
    type: record
    source: "@src-n9"         # @key = the ID that entity gets
    …
    from_diary: [diary 1998-04-11]
    body: |
      ## Transcript
      …
      Linked as @jan.          # @key also works in the body and in sentences
```

- Every entity has `key` and `type`; everything else is the header of the
  file, as in the schema (`schema/`). `body` is the Markdown body.
- Write `"@key"` in quotes in YAML. An `@word` that is no key (an e-mail
  address) stays as it is.
- IDs are new (`new_id` rules, ADR 0024); never write `id:`.
- Sessions go into `sessions/<year of date>/`.

## Running it

```
uv run .proavus/tools/bulk_import.py plan.yaml --dry-run
uv run .proavus/tools/bulk_import.py plan.yaml
```

- `--dry-run` lists the files, the validator's errors and warnings and the
  diary entries without a link – and writes nothing.
- Without it, the files are written only if the **whole batch** has no
  validation error, no diary entry is left without a link and no file
  exists yet. Otherwise nothing is written.
- The keys and the IDs they got are kept in `archive/import-keys.yaml`; a
  later plan can link them. A key can be used only once.
- The files look like hand-written ones (same YAML style as the examples).

## What the conversion must not do

- **Do not raise confidence.** Old notes say "the father was Václav" – that is
  a `possible` link until the record is read again (`read-once`) and the
  identity gate is passed in a session (ADR 0016). Write what the old notes
  claim as they claim it, cite the archive and keep `schema_gap` notes for
  what the schema cannot express yet.
- **Do not invent sources.** A fact from the tree without a source stays
  without citations (and possible), with a `schema_gap` or a question.
- **Living persons**: only name, sex, birth and relationships (rule 9) – an
  old tree often has more; leave it in `archive/`, do not import it.
- **No negative without its range.** "Not found" in the diary becomes a
  `coverage` with the book, the years, the pages and the names searched – or
  stays in the diary quote if those are not known.

From Python the same works directly (`proavuslib.bulk.Batch`: `add`,
`add_diary`, `preview`, `write`) – the tool is a thin wrapper around it.
