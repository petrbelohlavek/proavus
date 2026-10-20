# 0033 Čtení agentem a člověkem; potvrzuje jen člověk, který zápis četl

- **Stav:** přijato (2026-10-20)
- **Původně:** —
- **Doplňuje:** [ADR 0016](0016-pilot-without-reviewers-identity-gate.md)

## Kontext

Dosud `reading.read_by` neříkalo, zda zápis četl člověk, nebo agent zapsaný pod zkratkou člena. Brána identity (ADR 0016) má stát na tom, že rozhodující čtení viděl a potvrdil člověk.

## Rozhodnutí

- `reading.read_by`: jen členové (lidé), kteří zápis četli z obrazu; `reading.read_by_agent`: `true` nebo název modelu, četl-li ho agent. Potřeba je aspoň jedno z nich.
- `status: confirmed` vyžaduje `read_by` a `confirmed.by` musí být mezi nimi – potvrdit smí jen člověk, který zápis sám četl. Samotné čtení agentem nikdy nepotvrdí.
- Brána identity bere zápis jako potvrzený jen při splnění obojího.

## Důsledky

Stávající data: kdo je v `read_by`, platí za člověka. Kde první čtení dělal agent, doplní se `read_by_agent` (migrace to poznat nemůže). Skilly zapisují první čtení agentem jako `read_by_agent`, člena přidají do `read_by` až po jeho vlastním čtení výřezu.
