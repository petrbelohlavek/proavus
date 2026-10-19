# {{TITLE}}

Private family repository built with [Proavus](https://github.com/petrbelohlavek/proavus)
– evidence-first genealogy with AI. **This repository must stay private.**

## Your first session

1. Open this folder in the Claude app (Code tab).
2. Type `/start`. Claude downloads what others added, shows open questions
   and asks what you want to research.
3. Research with Claude: it reads records with you and writes everything
   into files with source citations.
4. Type `/end`. Claude checks the data, writes the session record with the
   next step and saves everything.

You never need to use git yourself. If something does not work, tell
Claude what happened.

## Rules in one breath

Question first · no statement without a source · transcribe before you
interpret · a person named in a record is not automatically a person in the
tree · identity needs a second reading · an index is not proof of absence ·
write conflicts down · protect the living · nothing here is ever published.

Full rules: `.proavus/method/rules.md`.

## Where things are

| Folder | Contents |
|---|---|
| `questions/` | research questions (one file each) |
| `sessions/YYYY/` | what was searched in each session and the next step |
| `coverage/` | what was searched where – including negative results |
| `records/` | transcripts of register entries; `evidence/` small image crops |
| `people/`, `relationships/`, `assertions/` | the tree and the facts behind it |
| `conflicts/`, `places/`, `sources/`, `oral/`, `decisions/`, `chronicle/` | disagreements, places, sources, oral testimony, family decisions, milestones |
| `archive/` | older material, frozen |
| `.proavus/` | pinned copy of the Proavus tools – do not edit (managed by `/proavus:upgrade`) |

`START-HERE.md` and `views/` are generated on your computer and are not
saved in git.
