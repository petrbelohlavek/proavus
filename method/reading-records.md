# Reading records

How to turn an image of a register entry into a `record` file that others
can check. Rules 3–5 of [rules.md](rules.md) in practice.

## 1. Locate before you read

Write the locator first, while the image is open: source (book), page as
shown by the portal, folio with side (`23r`, `23v`), entry number, image
number, URL and access date. Page and folio often drift apart inside one book
– record both; never compute one from the other without calibration points.

Save a small crop of the entry (JPEG, about 300 kB) as evidence. Full pages
stay in the archive and are cited, not copied (check the terms of use of the
source).

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

Godparents, witnesses and neighbours (FAN) are often the key to identity –
record them all, not only the family.

## 5. Reading state

A new record is `read-once`. A reading that decides identity (a name, a
house number, a date that separates two candidates) must be read a second
time, carefully, from the crop – by the same researcher in a later moment or
by another member. Then set `status: confirmed` with `confirmed: {by, on}`.
If two readings disagree, set `disputed` and open a conflict.

Typical traps:

- Kurrent letters that look alike (`e`/`n`, `h`/`f`, `s` forms) and digits
  (`1`/`7`, `4`/`9`);
- a name in the margin added years later (a marriage, death or legitimation
  note) – it is a separate statement with its own date;
- the index of a book missing an entry that exists – read the pages;
- similar names in the same village and decade (namesakes) – compare house
  numbers, parents and godparents before linking.

## 6. Hand over

Record the search in coverage (found or not), link the record from the
session, and write the next step. Tasks a machine cannot do (logging in to a
portal, paying a fee, writing to an archive) go to `human_tasks` with the
exact address of the record.
