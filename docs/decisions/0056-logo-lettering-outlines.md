# 0056 Nápis loga křivkami z otevřeného písma Gelasio

- **Stav:** přijato (2026-10-22)
- **Původně:** —
- **Upřesňuje:** [ADR 0007](0007-name-and-brand.md) (nápis převést na křivky)

## Kontext

Nápis „Proavus“ a podtitul v `proavus-logo.svg`, `proavus-logo-dark.svg`
a `proavus-social.svg` byly text v systémovém písmu Georgia. Na počítači bez
Georgie (Linux, část Androidu) se logo vykreslí jiným písmem a s jinou
šířkou; kontrolní seznam před zveřejněním (architektura, kap. 11) a ADR 0007
proto žádají křivky. Georgia je písmo Microsoftu a jeho soubor do repa
nepatří; zvažováno: křivky přímo z Georgie (vyžaduje písmo a jeho licenční
podmínky), nebo otevřené písmo stejných rozměrů.

## Rozhodnutí

- Nápis kreslí otevřené písmo **Gelasio** Regular 1.008 (SIL OFL 1.1),
  navržené jako metricky shodná náhrada Georgie: šířka nápisu, účaří
  a rozvržení zůstávají, tvary písmen jsou velmi blízké.
- V souborech loga není `<text>`, jen skupina `<g id="lettering">` s
  křivkami; přístupný název nese dál `aria-label` a `<title>`.
- Křivky kreslí `brand/lettering.py` (fontTools + HarfBuzz, s vyrovnáním
  párů jako prohlížeč; při prostrkání bez ligatur) z tabulky `LETTERING`.
  Soubor písma se do repa neukládá; skript ho ověří podle sha256.
- `proavus-social.png` je znovu vyexportovaný z nového SVG.

## Důsledky

- Logo vypadá všude stejně a nepotřebuje žádné písmo. OFL se vztahuje na
  písmo, ne na kresbu z něj; logo zůstává pod vlastní licencí
  (`LicenseRef-Proavus-Brand`, ADR 0012).
- Změna nápisu = upravit `LETTERING`, spustit skript s písmem, znovu
  vyexportovat PNG; test hlídá, že v logu není text ani odkaz na písmo.
- Obrázek dvou repozitářů v `docs/images/` (ADR 0053) má nápisy dál
  v Georgii; převod je samostatný krok.
