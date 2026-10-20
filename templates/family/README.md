# {{TITLE}}

Private family repository built with [Proavus](https://github.com/petrbelohlavek/proavus)
– evidence-first genealogy with AI. **This repository must stay private.**

## Every research session

1. In the Claude app (Code tab) start a **new session in this folder** –
   the folder name is shown under the message box and in the sidebar. Never
   in the `proavus` framework folder.
2. Type `/proavus:start` as the first message (type `/proavus:` and pick it
   from the list). Claude checks that this repository is private, downloads
   what others added, shows the check result, open questions and the last
   next step, and asks what you want to research.
3. Research with Claude: it reads records with you and writes everything
   into files with source citations. It never confirms an identity, a new
   parent or "proved" without your clear yes.
4. Type `/proavus:end` as the last message. Claude writes the session record
   with the next step, asks you about what needs your decision, checks the
   data (0 errors) and saves everything to GitHub.

You never need to use git yourself. If something does not work, tell
Claude what happened. (`/proavus:init` created this repository; it is not
needed again.) When `/proavus:start` says the Proavus copy is older than
the plugin, type `/proavus:upgrade` in a session in this folder: it shows
what changes, asks about new settings and updates the framework's files.

### If you forget

- **`/proavus:start`** – the rules still apply (Claude reads `AGENTS.md` in
  every session), but the privacy check, the download of others' work, the
  overview and the claim of the question did not happen. Type
  `/proavus:start` whenever you notice.
- **`/proavus:end`** – nothing is lost, but the work stays only on your
  computer: not saved, not backed up, not visible to others, and the next
  session does not know the next step. Open a session in this folder and
  type `/proavus:end` – it saves what is in the files. If `/proavus:start`
  stops because of unsaved changes, that is the reason: run
  `/proavus:end` first.

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
| `inquiries/` | letters and requests to offices, archives and parishes, with their state and answer |
| `archive/` | older material, frozen |
| `.proavus/` | pinned copy of the Proavus tools – do not edit (only `/proavus:upgrade` replaces it) |

`START-HERE.md` and `views/` are generated on your computer and are not
saved in git.
