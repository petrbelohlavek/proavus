# 0064 Režim přístupu u zdroje a zákonné lhůty matrik

- **Stav:** přijato (2026-10-24)
- **Původně:** —
- **Doplněno:** [ADR 0065](0065-archive-fetch-source-access.md) (archive_fetch čte `source.access`)
- **Doplňuje:** [ADR 0041](0041-archive-portals.md),
  [ADR 0050](0050-region-at-and-portal-catalogue.md) (katalog portálů)

## Kontext

Katalog portálů (`regions/*/portals.yaml`) zná režim `automated`, `link`
a `manual`, zdroj ale neříkal, ze kterého portálu je, a nešlo zapsat knihu,
která na portálu chybí (je u matričního úřadu, jen na žádost). Mladší zápisy
matrik navíc nejsou volně přístupné: zákon č. 301/2000 Sb. dovoluje
nahlížet komukoli do zápisu narození po 100 letech, manželství
a partnerství po 75 a úmrtí po 30 letech od zápisu (Portál veřejné správy,
ověřeno 2026-10-24); kniha přechází do archivu podle jiné lhůty (úmrtí 75 let
od posledního zápisu). Hledání v rozsahu, který ještě není otevřený, pak
vypadá jako negativ, i když zápisy nikdo neukázal.

## Rozhodnutí

- `source.portal`: id z katalogu portálů; `source.access: {mode, held_by,
  note}` s režimy `automated`, `link`, `manual`, `on-site`, `request`,
  `none` a držitelem `archive`, `registry-office`, `parish`, `other`.
  Validátor: neznámý portál varování; režim zdroje, který dovoluje víc než
  jeho portál, chyba.
- Lhůty jsou právo regionu, ne jádro: `regions/cz/access.yaml`
  (`entry_access`, `book_transfer`, převod typů událostí), kopíruje se do
  `.proavus/`. Číslo paragrafu se v souboru neuvádí, dokud není ověřené
  v úplném znění zákona.
- `coverage.event`: druh hledaných zápisů. S daty rozsahů dává rok, od
  kterého jsou všechny hledané zápisy volně přístupné. Negativ přes rozsah,
  který ještě otevřený není, je varování („byly zápisy ukázány? jinak
  inaccessible nebo partial“). START-HERE vypíše nedostupná hledání s rokem
  otevření, a když lhůta uplynula, vyzve k novému hledání.
- `tools/access.py` (`proavuslib/access.py`), kopíruje se do `.proavus/`:
  `limit REPO --event E --year Y` a `source REPO SO-ID`.

## Důsledky

Přidání (minor verze, bez migrace). Výpočet je odhad, rozhoduje archiv nebo
úřad; osoby, kterým zákon zápis ukáže dřív, se tím nevylučují. Lhůty pro
Rakousko (`regions/at`) se doplní, až je výzkum bude potřebovat.
`archive_fetch.py` portál dál určuje podle adresy; režim zdroje zatím
nečte.
