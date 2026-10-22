# 0057 Nápisy v obrázku dvou repozitářů křivkami

- **Stav:** přijato (2026-10-23)
- **Původně:** —
- **Upřesňuje:** [ADR 0053](0053-readme-for-everyone.md) (obrázek v README),
  navazuje na [ADR 0056](0056-logo-lettering-outlines.md) (nápis loga křivkami)

## Kontext

Obrázek dvou repozitářů v README (`docs/images/proavus-architecture*.svg`)
měl čtyři nápisy jako text: „Proavus“ v Georgii a jména rodin
`proavus-novak`, `proavus-smith`, `proavus-muller` v neproporcionálním
systémovém písmu. Na počítači bez těchto písem se vykreslí jiným písmem
a jinou šířkou; ADR 0056 převod nechal jako samostatný krok.

Obrázek kreslí `docs/images/architecture.py` jen se standardní knihovnou
Pythonu a test ho spouští v dočasné složce bez závislostí a bez písem.
Kreslení písmen (fontTools, HarfBuzz) proto do něj patřit nemůže.

## Rozhodnutí

- „Proavus“ kreslí **Gelasio** Regular 1.008 (SIL OFL 1.1) jako v logu,
  jména rodin **DejaVu Sans Mono** 2.37 (licence Bitstream Vera, úpravy
  DejaVu volné dílo; dovoluje kopírovat, šířit i upravovat).
- `docs/images/lettering.py` (fontTools + HarfBuzz, kreslení převzaté
  z `brand/lettering.py`) z obou písem jednou vykreslí slova obrázku do
  `docs/images/lettering.json`: pro každé slovo křivku od počátku na účaří
  a šířku ze součtu posunů znaků s vyrovnáním párů. Písma se do repa
  neukládají; skript je ověří podle sha256 a jejich zdroj má v docstringu.
- `architecture.py` načte JSON a slova jen umístí a vycentruje (místo
  `text-anchor="middle"`); dál běží bez závislostí. Slovo bez křivek je
  chyba s návodem.
- V obrázku není `<text>` ani `font-family`; hlídá to test, který také
  kopíruje `lettering.json` vedle skriptu.

## Důsledky

- Obrázek vypadá všude stejně a nepotřebuje žádné písmo; přístupný popis
  nese dál `aria-label` a `<title>`.
- `lettering.json` je kresba z písem, ne písmo; má licenci obrázku
  (CC BY 4.0). Ukládá celá slova, ne jednotlivé znaky.
- Nové nebo změněné slovo = upravit `WORDS` v `lettering.py`, spustit ho
  s oběma písmy, pak `python3 docs/images/architecture.py`.
