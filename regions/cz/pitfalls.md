# Pitfalls of Czech sources (regional package cz)

Experience from research in Czech registers and archive portals. General
reading rules are in [`method/reading-records.md`](../../method/reading-records.md);
this page adds what is typical for the Czech lands. Examples here are
general – never names of a real family.

## Reading

- **`P` / `Š` / `Ř` / `R`**: in kurrent and in Czech hands of the 19th century
  these capitals look alike (an `Ř` or `Š` written with a small hook or
  none, an open `P`). A surname read as `P…` may be `Ř…` or `Š…` – search all
  variants (also in indexes, sorted by the wrong letter).
- **Age column** in death registers: separate columns or a heading with
  years / months / days; a value above 30 is always years, small numbers
  need the heading.
- **Margin notes** (marriage, death, legitimation, change of name) were added
  years later, often by another priest or a registry office – a statement
  with its own date (record `annotations`).

## Indexes and locators

- The number in an index (*index*, *rejstřík*) is usually the **page
  (pag.)**, sometimes the folio – check the index header and the page
  numbering of the book.
- **Page → image**: the portals number images, not pages; the offset moves
  inside a book, and some books have two pages on one image, others one.
  Write two anchors into the source's `image_map` and use
  `locate.py` (ADR 0061) – a formula such as page = 2 × image − 2 holds
  only for the book it came from.
- **Separate index books** (e.g. SOA Třeboň, digi.ceskearchivy.cz): the index
  is its own book and refers to "Kniha strana číslo" (book, page, entry) –
  open the referenced book; the index entry is not the record. Write it as
  a pointer of the index coverage (`pointers`, ADR 0060).

## Searching

- **Married women** under the husband's surname; widows sometimes under
  the late husband's.
- **Marriage of the parents**: also in the next book of the marriage series
  and in the bride's home parish (the wedding was usually held there).
- **Cemeteries**: maps and grave registers are incomplete; a grave shared by
  two people does not prove they were parent and child.
- **Guardianship files of illegitimate children** (*poručenské*, later
  *opatrovnické spisy*) were kept by the district court of the child's
  **domicile** (*domovská příslušnost*) – also for a child born abroad (e.g.
  in Vienna). Today they are in the State District Archive (*SOkA*) of that
  district: ask by e-mail (an `inquiry`; the answer is due within 30 days).
- **Domicile right** ("příslušný do …", "zuständig nach …"): record it as
  written with the participant (`domicile_as_written`, ADR 0051) – it tells
  which municipality and court dealt with the person.
- **Side branches** (godparents, witnesses): agree on a budget and a stop
  rule first (method/reading-records.md, §4).

## Archive portals

The catalogue with what the agent may do on each portal and notes from
research is [`portals.yaml`](portals.yaml)
(`uv run tools/archive_fetch.py portals --region cz`, ADR 0041, 0050).

| Portal | Automated access (`tools/archive_fetch.py`) |
|---|---|
| ARON – ARchiv ONline (Východočeské archivy) | book, list, get through its public interface; at most 10 images per call by default, a pause between images |
| Acta Publica (Moravský zemský archiv) | link only – the terms of use and the app's robots.txt do not allow automated access without the archive's consent; behind a Cloudflare check: the agent builds links, a person reads |
| Matricula Online (Czech dioceses among others) | link only – robots.txt forbids automated access to image pages and blocks AI agents |
| Digitální archiv Jihočeských archivů (SOA Třeboň) | none – a person searches |

- **Archive names change**: SOA Zámrsk is now *SOA v Hradci Králové,
  archivní oddělení Zámrsk* – cite the current name (the registers are on
  ARON).

- A **ZIP of a whole book** offered by a portal is usually in a lower
  resolution than the viewer; crops for evidence come from the single image
  (with about 10 % margin).
- Terms of use differ by portal: images are for research; publishing them
  (also in a family book or online) needs the owner's consent – write it
  into `decisions/` and cite the source.
