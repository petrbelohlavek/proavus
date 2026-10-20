# 0046 Rodinný stav účastníka jako samostatné pole

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

`participant.status_as_written` míchalo manželský/nemanželský původ („syn
nemanželský“, *legitimus*) s rodinným stavem („svobodný“, „vdova“). Jeden
zápis potřebuje obojí – sňatek nemanželského svobodného ženicha.

## Rozhodnutí

- `marital_status_as_written`: rodinný stav doslova (*svobodný*, *vdova*,
  *coelebs*, *Witwer*);
- `marital_status` (volitelně): normalizovaná hodnota ze slovníku
  `marital_statuses` – `single`, `married`, `widowed`, `divorced`; jen když ji
  zápis jasně uvádí;
- `status_as_written` zůstává pro původ a jiný stav (*syn nemanželský*,
  *Häusler*).

Postup rozdělení starých hodnot je v `method/reading-records.md` §4.
`/proavus:upgrade` vypíše účastníky, jejichž `status_as_written` vypadá jako
rodinný stav (česká, německá a latinská slova); rozdělí se jen s člověkem,
který zápis čte – automatická migrace by hádala.

## Důsledky

Jádro i slovník: přidání, menší verze. Stávající data projdou validací beze
změny (kombinované `status_as_written` platí dál).
