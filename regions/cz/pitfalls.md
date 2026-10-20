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
  inside a book. Check two anchors before relying on it.

## Searching

- **Married women** under the husband's surname; widows sometimes under
  the late husband's.
- **Marriage of the parents**: also in the next book of the marriage series
  and in the bride's home parish (the wedding was usually held there).
- **Cemeteries**: maps and grave registers are incomplete; a grave shared by
  two people does not prove they were parent and child.

## Archive portals

| Portal | Automated access (`tools/archive_fetch.py`, ADR 0041) |
|---|---|
| ARON – ARchiv ONline (Východočeské archivy) | book, list, get through its public interface; at most 10 images per call by default, a pause between images |
| Acta Publica (Moravský zemský archiv) | link only – the terms of use and the app's robots.txt do not allow automated access without the archive's consent |
| Matricula Online (Czech dioceses among others) | link only – robots.txt forbids automated access to image pages and blocks AI agents |

- A **ZIP of a whole book** offered by a portal is usually in a lower
  resolution than the viewer; crops for evidence come from the single image
  (with about 10 % margin).
- Terms of use differ by portal: images are for research; publishing them
  (also in a family book or online) needs the owner's consent – write it
  into `decisions/` and cite the source.
