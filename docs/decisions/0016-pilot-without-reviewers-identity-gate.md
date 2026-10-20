# 0016 Pilot bez schvalovatelů; brána identity v sezení

- **Stav:** přijato (2026-10-20); čtení agentem a člověkem upřesňuje [ADR 0033](0033-reading-by-agent-and-human.md)
- **Původně:** R21, R4

## Kontext

Na osobním účtu GitHubu nelze vynutit kontrolu změn; malý tým důvěryhodných lidí nepotřebuje schvalovací proces, ale chybné čtení se nesmí stát faktem.

## Rozhodnutí

V pilotu bez schvalovatelů a návrhů změn: Claude zapisuje přímo do hlavní větve (před uložením stáhne novinky), vše hlídá stroj a Claude. **Člověk jen u brány identity**, a to sám badatel v témže sezení: potvrzení údaje rozhodujícího o identitě z výřezu (`read-once` → `confirmed`) a potvrzení zásadní změny stromu (propojení identity, spojení osob, nový rodič, „prokázáno“) polem `confirmed: {by, on}`. Validátor nedovolí, aby zápis čtený 1× podpořil „prokázáno“, pravděpodobnou či prokázanou identitu nebo spojení osob. `/review` = dobrovolný přehled.

## Důsledky

Schvalovatelé a druhý čtenář jiným člověkem přichází až v cílovém stavu (ADR 0003).
