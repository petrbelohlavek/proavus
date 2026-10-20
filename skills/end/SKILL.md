---
name: end
description: End a Proavus research session – write the session record and next step, pass the identity gate, validate and save everything to the family repository. Use at the end of every research session.
disable-model-invocation: true
---

# End a research session

Answer in the user's language. Saving goes straight to the main branch of the
private family repository (pilot mode, Proavus ADR 0016) – the checks below
are what protect the data.

## 1. Session record

Write `sessions/<YYYY>/<S-ID>.md` (new ID with
`uv run .proavus/tools/new_id.py session <abbr>`): date, researcher, the
questions, coverage and records of this session, the result in one or two
sentences, **the next step**, `inquiries` sent or answered, and human
tasks with exact addresses as `{task, status: open, for: <abbr>}`. Ask
whether open tasks of earlier sessions (START-HERE lists them) were done:
set `status: done` or `dropped` with `by` and `on` – only on the user's
word. Show the result and next step to the user and adjust if they want.

## 2. Nothing searched is lost

Check that every search done today has a `coverage/` file – including
negative and "not accessible" results, with ranges and all name variants.

## 3. Identity gate

List, in plain words, what in this session needs the researcher's decision:

- records that decide an identity but are still `read-once`;
- new identity links, merges of persons, new parents, anything `proved`.

For each one ask explicitly. Only on a clear yes after the user's own look
at the crop add them to `reading.read_by`, set `confirmed: {by: <abbr>, on:
<today>}` (and `reading.status: confirmed`). Your own reading never
confirms anything. Otherwise keep it `read-once` / lower the confidence – that is a
perfectly good result.

## 4. Chronicle

If today brought a milestone (question answered or bounded, something proved,
persons merged, a major error corrected, a new line or member), propose a
short `chronicle/<CH-ID>.md`: what happened, why it matters, links. Write it
only after the user confirms.

## 5. Validate

```
uv run .proavus/tools/validate.py .
```

0 errors are required. Fix errors together with the user; explain warnings
(an unknown vocabulary value may be a real new case – note it as
`schema_gap` if unsure). Some warnings end with a decision only the user
makes – write it only on their word:

- a negative from an index only: page through the book later (human task),
  or accept it – `index_negative_accepted: {by, on, note}` in the coverage
  file with the reason;
- "may be the same person": a merge goes through the identity gate
  (`aliases`); namesakes get `distinct_from: [<P-ID>]` and the reason in the
  body;
- the same fact twice: join the citations into one assertion;
- vital status unknown: add what the warning asks for, if it is known.

## 6. Privacy and save

1. `uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" check-private .` –
   continue only with exit 0, or 5 (local only: commit but do not push).
2. `git pull --rebase` (on conflict stop and explain).
3. `git add -A`, then `git status --short`. If anything outside the data
   folders changed (`CLAUDE.md`, `AGENTS.md`, `.proavus/`, `.claude/`,
   `.github/`), ask before including it. `START-HERE.md` and `views/` are
   ignored by git – never force them in.
4. `git commit -m "Session <S-ID> (<abbr>): <short result>"`
5. `git push`

## 7. Close

Three lines: what was found, what is saved, the next step.
