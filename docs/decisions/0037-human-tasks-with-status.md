# 0037 Úkoly pro člověka se stavem

- **Stav:** přijato (2026-10-20); úkoly zadané textem upřesňuje [ADR 0039](0039-start-here-readable.md); vazbu na otázku přidává [ADR 0047](0047-tasks-per-question.md)
- **Původně:** —

## Kontext

`human_tasks` byly text. START-HERE ukazoval úkoly posledních pěti sezení bez ohledu na to, zda už jsou hotové; starší otevřené úkoly zmizely.

## Rozhodnutí

Úkol je `{task, status, for, by, on, note}`: `status` `open` / `done` / `dropped`, `for` komu je určen, `by` a `on` kdo a kdy ho uzavřel (u `done` a `dropped` povinné). Text bez stavu dál platí jako otevřený úkol. START-HERE a mapa ukazují otevřené úkoly ze všech sezení. Migrace 0.3.0 převede text na `{task, status: open}`.

## Důsledky

Uzavření úkolu = úprava souboru sezení, ve kterém vznikl (`/proavus:end`). Dopisy úřadům patří do `inquiry` (ADR 0036).
