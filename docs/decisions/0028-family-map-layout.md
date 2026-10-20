# 0028 Rozvržení mapy rodiny: sloupce generací, karty a detail v dialogu

- **Stav:** přijato (2026-10-20)
- **Původně:** —
- **Nahrazuje:** rozvržení stránky z [ADR 0027](0027-family-map.md); rozhodnutí o jednom soběstačném souboru, výchozí osobě, jistotě na čarách a žijících osobách platí dál.

## Kontext

První podoba mapy (strom vlevo, karta vpravo) se v praxi neosvědčila tak
jako mapa, kterou si badatel ručně vedl v pilotním výzkumu před přechodem na
Proavus (ADR 0013). Ta se dobře čte i tiskne: generace ve sloupcích, na kartě
to podstatné, detail až po kliknutí. Z ní se převzala jen struktura, žádná
data.

## Rozhodnutí

Stránka `views/mapa.html` má pořadí: nadpis s výchozí osobou a výsledkem
kontroly → „chipy“ se součty → legenda → strom → mřížka boxů.

- **Strom:** sloupce generací s popisky (výchozí osoba, rodiče, prarodiče …),
  karty 210 × 160 px. Karta: štítky (nevlastní, už ve stromu), značka **!** při
  otevřeném rozporu, jméno, povolání, druhá podoba jména, narození a úmrtí
  s místem; u žijících jen narození a „žijící“.
- **Barva levého okraje karty** = jak je osoba doložená: nejlepší QUAY jejích
  zobrazených tvrzení (ADR 0022) – 3 prvotní přímý doklad, 2 druhotný nebo
  nepřímý, 1 slabý, 0 zatím bez dokladu (čárkovaně). Neznámý rodič je prázdná
  čárkovaná karta.
- **Čáry** lomené od dítěte k rodičům, styl podle jistoty vztahu (beze změny),
  nevlastní fialově. Mezi dvěma vlastními rodiči, kteří mají vztah
  `partnership`, je štítek **⚭ rok** (u žijících bez data).
- **Detail osoby** v dialogu: narození, úmrtí, povolání, další podoby jména,
  rodiče, nevlastní rodiče, partneři, děti; pod tím údaje se zdroji, výskyty
  v záznamech, otevřené rozpory a otázky. Odkaz na osobu otevře její detail;
  adresa `#P-…` otevře detail přímo.
- **Boxy pod stromem:** otevřené rozpory, otevřené otázky, další kroky
  z posledních sezení, osoby mimo strom.
- Obsah detailů se vykresluje už v Pythonu (šablony `<template>`), ne jako
  datový objekt v JavaScriptu – co pravidlo 9 skryje, ve stránce vůbec není.

## Důsledky

Bez JavaScriptu je vidět strom a boxy, detail ne. Velký strom se dál jen
posouvá; vyhledávání a přiblížení přijdou, až je vyžádá výzkum.
