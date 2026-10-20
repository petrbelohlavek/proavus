---
name: start
description: Start a Proavus research session in a family repository – sync, check privacy and data, show open questions and pick what to work on. Use at the beginning of every research session.
argument-hint: "[question ID]"
disable-model-invocation: true
---

# Start a research session

Answer in the user's language, briefly. The user does not need to know git.

## 1. Is this a family repository?

The current folder must contain `repo.yaml` and `.proavus/`. If it contains
`.claude-plugin/marketplace.json` and no `repo.yaml`, it is the Proavus
framework: stop – family data never go there. If it is an empty or other
folder, offer `/proavus:init`.

## 2. Privacy check

```
uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" check-private .
```

- exit 0 – private, continue;
- exit 3 – public or a fork of proavus: **do not write anything**; explain
  and help make it private (or move the data to a new private repository);
- exit 4 – cannot tell (gh missing or logged out): help fix it; until then
  do not save or push anything;
- exit 5 – no remote yet: work locally, remind that the private repository
  still has to be created (step 7 of `/proavus:init`).

## 3. Get what others added

If there is a remote: `git pull --rebase`. If it reports a conflict, stop and
explain in plain words; resolve together, never discard others' work.

## 4. Status

```
uv run .proavus/tools/family_repo.py start-here .
```

Read `START-HERE.md` (generated, never edit or commit it). If it says the
Proavus copy is older than the plugin, tell the user and offer
`/proavus:upgrade` (they type it; it needs a clean state, so do it before
starting new work).
Read `AGENTS.md`, the family notes in `CLAUDE.md` and the binding rules
`${CLAUDE_PLUGIN_ROOT}/method/rules.md` (Czech: `rules.cs.md`).

## 5. Who is researching

Find the user's abbreviation in `repo.yaml` → `members`. If they are not
listed, ask for name and a 2–4 letter abbreviation and add them (with their
yes).

## 6. Choose the work

Show in a few lines: check result, open questions (with who is on them),
the last next steps and human tasks, what waits for a human (records read
once, conflicts). Ask what to work on today ($ARGUMENTS may name a question).

- Existing question: if someone else has claimed it, say so and ask.
  Otherwise set `claimed_by` and `status: in-progress`, then save right away
  so others see the claim: `git add questions/<file>`, `git commit -m "Claim
  <Q-ID> (<abbr>)"`, `git pull --rebase`, `git push`.
- New question: write `questions/<Q-ID>.md` with a new ID
  (`uv run .proavus/tools/new_id.py question <abbr>`), the title, an anchor
  record if one exists, and a plan: what this search can answer and what it
  cannot. Agree on it with the user.

## 7. During the session

Follow the method:

- Before searching a book, check `coverage/` – was it searched already, with
  which name variants?
- Record every search in `coverage/` (also negatives and "not accessible").
- Transcribe records per `${CLAUDE_PLUGIN_ROOT}/method/reading-records.md`:
  locator first, verbatim transcript with `[ ]`, then interpretation and
  participants.
- New files always with `new_id.py`; one entity = one file.
- **Identity gate:** never set `confirmed` (reading, identity link, merge,
  proved relationship) without the user's explicit yes in this session after
  looking at the crop.
- Three empty searches in a row → suggest a different kind of source.
- Tasks only a human can do (log-ins, fees, letters) – note them with the
  exact address for the session record.
- Family map on request (tree, "show me the ancestors"):
  `uv run .proavus/tools/build_views.py .` writes `views/mapa.html` (never
  committed) – tell the user to open it in a browser. It starts from
  `map.root` in `repo.yaml`; if that is missing, ask whose ancestors to show
  and add `map: {root: <P-ID>}` with their yes (or use `--root <P-ID>` once).
  If `.proavus/tools/build_views.py` is missing, the copy is older than 0.2.0:
  with the user's yes run
  `uv run "${CLAUDE_PLUGIN_ROOT}/tools/family_repo.py" install-tools .`
  and save the updated `.proavus/` in the next commit.

End with `/proavus:end`.
