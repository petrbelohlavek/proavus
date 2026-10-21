# Pitfalls of Austrian sources (regional package at)

Experience from research in Viennese registers and archives. General reading
rules are in [`method/reading-records.md`](../../method/reading-records.md);
what the portals allow and their notes are in [`portals.yaml`](portals.yaml)
(`uv run tools/archive_fetch.py portals --region at`). Examples here are
general – never names of a real family.

## Indexes and locators (Matricula Online)

- **The number in an index depends on the book**: a folio in one, page plus
  entry number in another. One book may start a new foliation every year,
  another counts folios through the years. Read the index header and check
  **two anchors in every section** before relying on the number.
- **Page ↔ folio ↔ image**: the offset between the viewer's image number
  (`pg`), the page and the folio changes **inside a book** (inserted sheets,
  a new year). Record all three in the locator (`image`, `page`, `folio`).
- **Where the index is**: at the beginning *and* at the end of a book. Big
  parishes kept **two volumes a year** (first and second half) – a missing
  entry may be in the other half.

## Reading

- **A child's baptism is the fastest way to the parents' marriage**: it
  often gives the father's date and place of birth and the date and parish
  of the parents' marriage.
- **Abbreviated parishes** ("Pfr. St. Jos. Wien II"): resolve them against
  all parishes of that district starting with the same letters, not the
  first that fits.
- **The wife's given name varies** between entries of one family (Maria /
  Anna Maria / Marie …) – never a deciding feature of identity.
- **Later notes in the margin**: marriage, death with the number of the
  Standesamt entry, leaving the church (event `church-exit`) – each one a
  record `annotation` with its own date.
- **Domicile right** ("zuständig nach …", Heimatrecht): record it as written
  with the participant (`domicile_as_written`, ADR 0051) – it points to the
  municipality whose files (and court) dealt with the person.

## Access limits

- **Books younger than 100 years** are blocked on Matricula ("aus
  gesetzlichen Gründen gesperrt") – also baptisms in hospital parishes. Write
  an `inquiry` to the parish or the diocesan archive.
- **Cremation**: the Catholic death entry is often missing – look for the
  burial (cemetery database) and the civil register (Standesamt, since 1938).
- Record a blocked book in coverage as `inaccessible`, never as a negative.

## Cemeteries, archives, newspapers

- **Friedhöfe Wien** (Verstorbenensuche): the date is the **burial date**,
  not the death date (an assertion of a burial, not of a death); older
  burials only in the historical mode; the detail shows the age at death
  and the grave (group / row / number). Results are not stable – repeat the
  search, save a screenshot with the date and write the query into coverage.
  Denominational cemeteries are not covered.
- **WStLA**: an e-mail gets only a procedural answer; research goes through
  the paid form "Archivbestände – Auskunft" (a rate per half hour, with a
  cap). **Standesamt** (since 1938): acknowledgement of receipt, fees;
  duplicate requests cost more. Each request is an `inquiry`, the fee a
  human task.
- **ANNO** full-text search misses death notices (Parte) – page through the
  issues after the death. **Lehmann** (address book) has no text layer –
  page through the alphabetical pages of each year (`page-through`).

## Side branches

Godparents and witnesses are often the key to identity (FAN), but each one
opens new books. Before following one, agree on a **budget** (e.g. two books
or one session) and a **stop rule** (e.g. "stop when the godparent's own
baptism is found or the budget is spent") and write them into the question's
plan (method/reading-records.md, §4).
