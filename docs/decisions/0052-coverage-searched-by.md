# 0052 Coverage: kdo hledal – člen sám, nebo agent na jeho pokyn

- **Stav:** přijato (2026-10-21)
- **Původně:** —
- **Upřesňuje:** [ADR 0033](0033-reading-by-agent-and-human.md), [ADR 0035](0035-coverage-query.md)

## Kontext

V pilotu hledali jednou člen sám (Matricula, kam agent nesmí), jindy agent
na jeho pokyn (ARON, databáze). `coverage.by` uvádí člena, takže z ní
nebylo poznat, kdo knihu skutečně prošel. Na tom záleží při hodnocení
negativu: agent a člověk přehlížejí jiné věci (agent čte jinak rukopis,
člověk se unaví) a negativ agenta je důvod k druhému průchodu. U čtení zápisu
to už rozlišujeme (`read_by` / `read_by_agent`, ADR 0033).

## Rozhodnutí

- `coverage.searched_by`: `member` (hledal člen uvedený v `by`) nebo
  `agent` (AI agent na pokyn člena v `by`); u agenta volitelně
  `agent_model`. `agent_model` bez `searched_by: agent` je chyba schématu.
- Pole je **v jádře** (coverage je jádro a údaj není regionální), ale
  **volitelné**: starší coverage zůstává platná, migrace se nedělá – zpětně
  to poznat nejde. `by` zůstává povinné: za hledání odpovídá vždy člen.
- `/proavus:start` a `/proavus:end` ho zapisují u každého nového hledání.

## Důsledky

- Testy na fiktivní rodině: obě hodnoty, `agent_model` jen s `agent`,
  neznámá hodnota, starší coverage bez pole.
- Validátor zatím chybějící `searched_by` nehlásí (staré záznamy by
  zahltil varováními); pokud se ukáže potřeba, přijde varování pro nové
  záznamy novým ADR.
