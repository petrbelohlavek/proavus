# Reading records

How to turn an image of a register entry into a `record` file that others
can check. Rules 3–5 of [rules.md](rules.md) in practice.

## 1. Locate before you read

Write the locator first, while the image is open: source (book), volume
(`volume`, as written – volumes of one source need not follow each other by
date; list them in `source.volumes`), page as shown by the portal, folio
with side (`23r`, `23v`), entry number, image number, URL and access date.
Page and folio often drift apart inside one book – record both; never
compute one from the other without calibration points.

- **An index number is often a page (pag.), not a folio.** Check the header
  of the index and a page or two of the book before you go to the entry.
- **Page → image needs two anchors.** The offset between the printed page
  and the image number in the viewer changes (inserted sheets, missing or
  double scans), and so does the number of pages on one image; a formula
  from another book does not hold. Read the page number on two images – near
  the entry and further away – and write them as anchors into the source's
  `image_map` (per volume, or per `part` of a book with its own page
  numbering; `unit: folio` for a book numbered in folios), with who read
  them and when (ADR 0061, 0068). `uv run .proavus/tools/locate.py
  <SO-ID> --page N [--volume V] [--part P]` then gives the image: exact, between two
  anchors, or only an estimate outside them. When the image shows another
  page, there is a break: add an anchor there. The validator compares every
  record with a page and an image against the map.

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

- **Domicile right** (*domovská příslušnost*, *Heimatrecht*: "příslušný do
  …", "zuständig nach …"): with the regional extension `cz` or `at` write
  it as written into `domicile_as_written` and, as interpretation, the
  place into `domicile_place` (ADR 0051). It names the municipality – and
  the district court – that kept the person's files.

Godparents, witnesses and neighbours (FAN) are often the key to identity –
record them all, not only the family. **Following** one of them into other
books is a side branch: agree first on a **budget** (e.g. two books or one
session) and a **stop rule** (e.g. "stop when their own baptism is found,
or when the budget is spent") and write both into the question's plan
(`next_sources`, or `will_not_answer` for what stays out). When the budget
is spent, stop and decide with the user – do not drift.

## 5. Reading state

A new record is `read-once`. Record who read it and when: members (people)
in `read_by` (the first reader first), a reading by an AI agent as
`read_by_agent` (the model), the day in `read_on` – never write a member
into `read_by` for a reading they did not do themselves.

A reading that decides identity (a name, a house number, a date that
separates two candidates) must be read a second time from the crop by a
person (ADR 0059). The second reading reads the **decisive items** again,
after the first reading and apart from it. There are three ways:

- **after the agent** (`member-after-agent`) – the usual way when one person
  researches with the agent: the agent read first; it names the items and
  asks the person to read them from the crop **without showing its own
  reading**; only then the two readings are compared;
- **the same member later** (`member-later`): the member read it first
  themselves and reads the items again on a later day (`read_on` before
  `confirmed.on`);
- **another member** (`second-member`): `read_by` lists the first reader
  first, `confirmed.by` is the other one.

Agreeing with a transcript you have just seen is not a second reading. When
the readings match, add the person to `read_by` and set `status: confirmed`
with

```yaml
confirmed:
  by: ab
  on: 2026-10-24
  basis: member-after-agent
  from: crop
  checked: [house number of p1, date of baptism, name of the father]
```

Only a member who read the entry may confirm it. If the readings disagree,
set `disputed` and open a conflict. The identity link that rests on the
reading (`assertion.confirmed`) is a different thing: a decision of the
researcher in the session, which the same person who read the entry may
make.

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
session, and write the next step. An index and the book it points to are two
sources and two searches: one coverage for the index (what it gave), one for
the pages of the book you read – the record found there goes into the
book's `found`. What the index gives is a **pointer**, not a record (ADR
0060): write it into the index coverage as `pointers` – the name as the
index gives it and where it leads (`to: {source, volume, page, entry}`),
never as participants or an assertion – and once the book is searched, set
`followed` to the book's coverage. A year or date in the index
(`date_as_written`) is a hint; the book decides.

Searched one part of a book (a village, a section, a letter
of the index)? Name it in the range's `part`; when the first page or image
of the part is not known, start the range with `..` (`images ..-250`). An
index that really covers less than the archive says (the section of a
letter starts years later) gets `index_covers` – the years outside it are
not searched by that coverage.

An entry that may belong to the family but is not shown to is a **lead**:
add it to the question's `leads` with where it is (book, part, image,
entry, URL), why it is suspected, who found it and when, `status: open` –
no names of other people and no transcript. Close it later: `confirmed`
with the `record` written from it, or `rejected` with a note why, both
with `closed: {by, on}`. Tasks a machine cannot do (logging in to a
portal, paying a fee) go to `human_tasks` with the exact address of the
record, as `{task, status: open, question: <Q-ID>}` (and `conflict` or
`inquiry` if the task serves one); close them later with `status: done` or
`dropped`, `by` and `on`. A letter or request to an office, archive or
parish is an `inquiry` (`inquiries/`) – addressee, date sent, state, and
later the answer and the records made from it.
