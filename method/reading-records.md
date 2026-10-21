# Reading records

How to turn an image of a register entry into a `record` file that others
can check. Rules 3–5 of [rules.md](rules.md) in practice.

## 1. Locate before you read

Write the locator first, while the image is open: source (book), page as
shown by the portal, folio with side (`23r`, `23v`), entry number, image
number, URL and access date. Page and folio often drift apart inside one book
– record both; never compute one from the other without calibration points.

- **An index number is often a page (pag.), not a folio.** Check the header
  of the index and a page or two of the book before you go to the entry.
- **Page → image needs two anchors.** The offset between the printed page
  and the image number in the viewer changes (inserted sheets, missing or
  double scans). Verify it at two points – near the entry and further away –
  before trusting it; write the anchors into the session.

Save a small crop of the entry (JPEG, about 300 kB) as evidence, with about
10 % margin around the entry so that the column headings or the neighbour
lines that prove where it sits stay visible. Full pages stay in the archive
and are cited, not copied (check the terms of use of the source). A download
of the whole book (ZIP) is often in a lower resolution than the viewer –
crop from the single image.

Downloading images with `tools/archive_fetch.py` (ADR 0041) only after the
researcher has said yes to the list of images (`get --dry-run`), into a
folder outside the repository; some portals allow no automated access at all
– then the tool only gives the link.

## 2. Transcribe verbatim

Under `## Transcript` copy the entry exactly:

- keep the original language, spelling, abbreviations and capitalisation
  (`Joañes`, `filius legit.`), Latin, German or Czech as written;
- keep the column order of the register; separate columns with ` | `;
- mark every uncertain reading in square brackets: `Kmotr[ovsky]`,
  `[1864 or 1867]`, `[illegible]`; list the uncertain readings in
  `reading.uncertain`;
- do not expand, translate or correct anything here.

## 3. Interpret separately

Under `## Interpretation` write what the entry means: expanded abbreviations,
the date in modern form, normalised names, translated occupations. An
interpretation may be wrong; the transcript lets the next reader see why.

## 4. Fill in the participants

List everyone named in the entry as a participant with a key (`p1`, `p2` …),
the name **as written**, the role (child, father, mother, godparent, witness,
midwife, officiant …) and what the record says about them: age, residence and
house number, occupation, religion, status. Participants are not persons in
the tree; the link is made later by an identity assertion.

- **Roles relative to the principal:** the spouse's parents are
  `spouse-father` / `spouse-mother` (a death entry naming the widow's
  father); a grandfather or grandmother whose side or whose grandparent is
  not stated is `grandfather` / `grandmother` with a `note` saying whose
  (e.g. the groom's maternal grandfather of an illegitimate groom). `other`
  only when no role fits – say what it is in `note`.
- **Status and marital status are two fields** (ADR 0046):
  `status_as_written` for origin and other status (*syn nemanželský*,
  *legitimus*, *Häusler*), `marital_status_as_written` for the marital
  status as written (*svobodný*, *vdova*, *coelebs*, *Witwer*) and, if the
  record states it clearly, `marital_status`: `single`, `married`,
  `widowed` or `divorced`. One entry may need both: *syn nemanželský,
  svobodný* → `status_as_written: syn nemanželský`,
  `marital_status_as_written: svobodný`, `marital_status: single`.
- **Older records** keep both in `status_as_written`; that stays valid.
  `/proavus:upgrade` lists the participants whose `status_as_written` looks
  like a marital status – split them only together with the person who reads
  the record, keep the wording exactly as written, and never guess a
  normalised value the record does not state.

Godparents, witnesses and neighbours (FAN) are often the key to identity –
record them all, not only the family.

## 5. Reading state

A new record is `read-once`. Record who read it: members (people) in
`read_by`, a reading by an AI agent as `read_by_agent` (the model) – never
write a member into `read_by` for a reading they did not do themselves. A
reading that decides identity (a name, a house number, a date that separates
two candidates) must be read a second time, carefully, from the crop – by a
person: the same researcher in a later moment or another member. Then add
them to `read_by` and set `status: confirmed` with `confirmed: {by, on}`;
only a member who read the entry may confirm it. If two readings disagree,
set `disputed` and open a conflict.

Typical traps:

- Kurrent letters that look alike (`e`/`n`, `h`/`f`, `s` forms) and digits
  (`1`/`7`, `4`/`9`); capitals of surnames are mistaken for each other
  (in Czech registers `P`/`Š`/`Ř`/`R`, see `regions/cz/pitfalls.md`) – search
  the variants;
- a note in the margin is **later** than the entry (a marriage, death or
  legitimation note, often in another hand) – it is a separate statement with
  its own date: transcribe it and add it to `annotations` (text, hand, event
  and its date), with its own crop in `crops`; never date the entry by it;
- an age column: the unit is in the column heading (years / months / weeks /
  days); a number above 30 can only be years – a number like 2 or 6 needs
  the heading;
- the index of a book missing an entry that exists – read the pages;
- similar names in the same village and decade (namesakes) – compare house
  numbers, parents and godparents before linking.

Where else to look:

- **married women** appear under the husband's surname in later records
  (children's baptisms, death) – search both the birth and the married name;
- **the parents' marriage** may be in the following book, not in the one
  of the first child's baptism (marriages are entered where they took place,
  and books overlap) – search the next book of the marriage series and the
  bride's parish;
- **graves**: cemetery maps and registers of graves are often incomplete,
  and a shared grave does not prove a parent–child relationship – use them
  as a clue, cite them with information `secondary` or `undetermined`.

## 6. Hand over

Record the search in coverage (found or not), link the record from the
session, and write the next step. Tasks a machine cannot do (logging in to a
portal, paying a fee) go to `human_tasks` with the exact address of the
record, as `{task, status: open, question: <Q-ID>}` (and `conflict` or
`inquiry` if the task serves one); close them later with `status: done` or
`dropped`, `by` and `on`. A letter or request to an office, archive or
parish is an `inquiry` (`inquiries/`) – addressee, date sent, state, and
later the answer and the records made from it.
