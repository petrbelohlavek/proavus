# 0020 Kronika výzkumu

- **Stav:** přijato (2026-10-20)
- **Původně:** R25

## Kontext

Historie gitu a deník sezení nevyprávějí, jak rodokmen vznikal; noví členové potřebují čitelný příběh včetně slepých uliček.

## Rozhodnutí

`chronicle/` v rodinném repu, 1 soubor za milník (zásadní nález, zlom hypotézy, opravená velká chyba, uzavřená otázka, nový člen nebo linie, přechod). Stroj milník rozpozná, Claude navrhne zápis, badatel ho v sezení potvrdí. Časová osa `views/history.md` se generuje na požádání.

## Důsledky

Schéma `chronicle` je ve v0 minimální (datum, typ milníku, název, potvrzení).
