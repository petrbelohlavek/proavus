# 0012 Licence podle částí repa, označení REUSE

- **Stav:** přijato (2026-10-20)
- **Původně:** R17

## Kontext

Text, kód, šablona kopírovaná do dat rodin a logo potřebují různé licence.

## Rozhodnutí

Metodika a dokumentace CC BY 4.0; kód MIT; schéma, slovníky, šablona rodinného repa, manifest pluginu a drobná konfigurace CC0 1.0; název a logo všechna práva vyhrazena (`LicenseRef-Proavus-Brand`); převzaté části pod původní licencí. Označení přes `REUSE.toml`, plné texty v `LICENSES/`, kontrola `reuse lint` v CI.

## Důsledky

Rodina nemá povinnost uvádět autora ve vlastních datech. Příspěvky přicházejí pod licencí dané složky. Data rodiny licenci nemají.
