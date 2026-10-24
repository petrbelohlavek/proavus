# 0059 Co je druhé čtení a jak se zapíše

- **Stav:** přijato (2026-10-24)
- **Původně:** —
- **Upřesňuje:** [ADR 0016](0016-pilot-without-reviewers-identity-gate.md)
  (brána identity), [ADR 0033](0033-reading-by-agent-and-human.md) (čtení
  agentem a člověkem)

## Kontext

Brána identity chce potvrzené čtení: `confirmed.by` musí být mezi `read_by`
(ADR 0033). Validátor ale nepoznal, že čtení byla dvě – `read_by: [ab]`
a `confirmed: {by: ab}` prošlo i po jediném čtení, které člověk hned
potvrdil. U rodinného pátrání čte většinou jeden člověk s agentem, takže
„druhý člen“ často není a „tentýž badatel později“ nebylo nijak zapsané.
Navíc se pletlo potvrzení čtení (dvě čtení) s potvrzením identity
(rozhodnutí badatele).

## Rozhodnutí

- **Druhé čtení** je čtení rozhodujících údajů zápisu (jméno, číslo domu,
  datum, rodiče – to, co odděluje kandidáty) člověkem z výřezu nebo snímku,
  po prvním čtení a nezávisle na něm. Souhlas s přepisem, který člověk
  viděl, druhé čtení není. Tři cesty (`confirmed.basis`):
  - `member-after-agent` – první četl agent (`read_by_agent`), člen přečte
    údaje naslepo: agent je jmenuje a své čtení ukáže až po odpovědi;
  - `member-later` – tentýž člen jiný den; `reading.read_on` (den prvního
    čtení) musí být před `confirmed.on`;
  - `second-member` – jiný člen; `read_by` uvádí prvního čtenáře první
    a `confirmed.by` je ten druhý.
- `confirmed.checked`: přečtené rozhodující údaje (povinné s `basis`),
  `confirmed.from`: `crop` nebo `image`. Nová definice
  `record#/$defs/reading_confirmation`; `assertion.confirmed` zůstává
  `{by, on, note}` – identita je rozhodnutí a smí ho udělat tentýž člověk,
  který zápis četl.
- Validátor: nesoulad `basis` s `read_by`, `read_by_agent` a `read_on` je
  chyba; potvrzení před prvním čtením je chyba; potvrzení bez `basis` je
  zatím jen varování (starší data). `upgrade-plan` vypíše potvrzená čtení
  bez `basis`; doplňují se jen podle odpovědi člověka, který potvrzoval.
- Pravidlo 5 (`method/rules.md`, `rules.cs.md`), `reading-records.md` §5,
  blok `AGENTS.md` rodinné šablony a skilly `start` a `end` popisují čtení
  naslepo.

## Důsledky

Přidání (minor verze, bez migrace). To, že čtení bylo opravdu naslepo,
v datech ověřit nejde – hlídá to postup ve skillu. Z varování „bez basis“ se
může stát chyba v 1.0, až budou starší data doplněná.
