# 0065 `archive_fetch.py` čte zdroj a jeho režim přístupu

- **Stav:** přijato (2026-10-25)
- **Původně:** —
- **Doplňuje:** [ADR 0041](0041-archive-portals.md),
  [ADR 0064](0064-access-and-time-limits.md)

## Kontext

ADR 0064 zavedl `source.access` (režim, držitel, poznámka), ale
`archive_fetch.py` portál dál určoval jen podle adresy. Kniha, kterou portál
umí, ale která je podle zdroje jen v badatelně nebo na žádost (svazek není
digitalizovaný, kniha je u matričního úřadu), by se dala stáhnout nebo
odkázat, jako by přístupná byla; a agent musel adresu knihy opisovat ze
zdroje ručně.

## Rozhodnutí

- `book`, `list`, `link` a `get` berou místo adresy `--source SO-ID`
  (s `--repo`, výchozí `.`, a `--volume V`): adresa je `url` svazku, jinak
  `url` zdroje. Zdroj se čte přímo ze `sources/` (jen `pyyaml`, bez
  validátoru – nástroj zůstává samostatný).
- Režim zdroje se uplatní **před** portálem: `book`, `list` a `get`
  potřebují `automated`, `link` potřebuje `link` nebo `automated`. Co zdroj
  nedovoluje, nástroj odmítne s kódem 3 a portálu se ani nedotkne. Zdroj
  nikdy nerozšíří, co dovoluje portál – podmínky portálu platí dál.
- Bez `--source` se nástroj chová jako dosud.

## Důsledky

Přidání (bez změny schématu). Skilly `start` a `registers` dávají přednost
`--source`.
