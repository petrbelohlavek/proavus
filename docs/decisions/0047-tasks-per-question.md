# 0047 Úkol patří k otázce; poslední sezení jen z práce na otázce

- **Stav:** přijato (2026-10-21)
- **Původně:** —
- **Upřesňuje:** [ADR 0037](0037-human-tasks-with-status.md), [ADR 0039](0039-start-here-readable.md)

## Kontext

START-HERE přiřazoval úkol každé otázce, kterou sezení uvádělo v `questions`.
Sezení o dvou otázkách tak ukázalo své úkoly u obou a ještě jednou v bloku
„Waiting for a human“. Stejně „poslední sezení“ otázky: stačilo, že ji
sezení uvedlo, i když dělalo něco jiného – jeho další krok pak u otázky
neseděl. Úkol k zodpovězené otázce zůstal otevřený bez upozornění a dopisy
úřadům se dál psaly jako úkoly místo `inquiry` (ADR 0036).

## Rozhodnutí

- **Úkol** (`human_tasks`) smí nést `question` (otázka, které slouží),
  volitelně `conflict` a `inquiry` (např. poplatek za dotaz). Přidání,
  jádro (ADR 0015).
- **START-HERE** ukáže každý otevřený úkol jednou: u otevřené otázky z jeho
  `question`; ostatní (bez otázky, nebo s otázkou, která už otevřená není –
  pak s jejím stavem) v bloku „open human tasks without an open question“.
  U úkolu je i rozpor nebo dotaz, ke kterému patří.
- **Poslední sezení otázky** je jen sezení, které ji má v `questions` a na
  otázce opravdu pracovalo: je to jeho jediná otázka, nebo má coverage té
  otázky, zápis otázky (kotva nebo nález jejího hledání), dotaz k otázce,
  nebo úkol s jejím `question`.
- **Validátor** varuje u otevřeného úkolu, jehož otázka je `answered`,
  `bounded` nebo `abandoned` (uzavřít, nebo převést k otevřené otázce), a
  radí založit `inquiry`, když text otevřeného úkolu bez `inquiry` obsahuje
  e-mail nebo slova odpověď / dotaz / žádost (v jakémkoli tvaru, bez ohledu
  na diakritiku).
- **Migrace 0.4.0** doplní `question` tam, kde je jednoznačná: dotaz úkolu
  se týká jediné otázky, jinak má sezení jedinou otázku. Jinde nic nehádá;
  textový úkol, kterému doplní otázku, převede na `{task, status: open,
  question}`.

## Důsledky

Při zápisu úkolu (`/proavus:end`) agent uvede otázku. Úkoly ze sezení o více
otázkách bez vazby zůstanou v samostatném bloku, dokud je někdo nepřiřadí.
Mapa rodiny ukazuje úkoly beze změny.
