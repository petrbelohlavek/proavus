# 0009 Rodinné repo zakládá `/init` a aktualizuje `/upgrade`

- **Stav:** přijato (2026-10-20)
- **Původně:** R14

## Kontext

Tlačítko GitHubu „Use this template“ kopíruje celé repo, ne podsložku se šablonou.

## Rozhodnutí

Šablona rodinného repa je v pluginu (`templates/family/`). `/init` založí nové soukromé repo, naplní ho šablonou a ověří, že je soukromé. `/upgrade` aktualizuje soubory frameworku v rodinném repu (blok `proavus:begin/end`, workflow, `.proavus/`, `schema_version`) a při změně schématu spustí `migrate.py`.

## Důsledky

Rodina nikdy neupravuje soubory frameworku ručně; framework nikdy nemění soubory rodiny.
