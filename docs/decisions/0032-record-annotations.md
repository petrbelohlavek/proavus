# 0032 Pozdější poznámky na okraji zápisu

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Matriky nesou pozdější poznámky – sňatek, úmrtí, legitimace, změna jména – často jinou rukou a s jiným datem. Je to samostatné tvrzení s vlastním datem (method/reading-records.md); dosud se musely psát do `schema_gap`.

## Rozhodnutí

`record.annotations`: seznam poznámek `{text, position, hand, written, event, event_date, event_place, interpretation}`. `text` je doslovný přepis (s `[ ]`), `hand` čí ruka, `written` kdy byla poznámka zapsána, `event` (slovník `event_types`) a `event_date` o čem a kdy podává zprávu. Doslovný text patří také do `## Transcript`.

## Důsledky

Jádro, přidání. Fakt z poznámky se dál zapisuje jako tvrzení s citací zápisu; poznámka sama nic nedokazuje.
