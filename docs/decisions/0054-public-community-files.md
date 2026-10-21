# 0054 Veřejná výbava: CONTRIBUTING, pravidla chování, SECURITY, šablony úkolů

- **Stav:** přijato (2026-10-21)
- **Původně:** —

## Kontext

Kontrolní seznam před zveřejněním (architektura, kap. 11; ADR 0010) žádá
veřejnou výbavu: CONTRIBUTING, pravidla chování, `SECURITY.md` a šablony
úkolů. Po přepnutí na veřejné je každý úkol, komentář i pull request
veřejný a u rodinného bádání hrozí, že někdo v dobré víře vloží jména,
data nebo snímek zápisu své rodiny – i žijících příbuzných. Zvažováno:
převzít Contributor Covenant doslovně, nebo krátká vlastní pravidla;
volné úkoly, nebo jen formuláře.

## Rozhodnutí

- **`CONTRIBUTING.md`** (anglicky, technické čtení jako `TECHNICAL.md`,
  ADR 0053): na prvním místě zákaz skutečných dat rodiny ve všech
  příspěvcích a jak popsat situaci smyšlenými osobami; co přispívat podle
  ADR 0013; jak pracovat (hooky s vlastním seznamem jmen přispěvatele mimo
  repo, testy, REUSE); příspěvky pod licencí části, kam patří (ADR 0012).
  Podrobná pravidla zůstávají v `AGENTS.md`.
- **`CODE_OF_CONDUCT.md`:** krátká vlastní pravidla s ohledem na rodinná
  témata (úcta k lidem v záznamech, soukromí, žádná genealogie pro
  rasovou nadřazenost), inspirovaná Contributor Covenant; doslovný text
  by nesl cizí autorství a délku, kterou laik nečte.
- **`SECURITY.md`:** za bezpečnostní problém se počítá i únik rodinných
  dat (do frameworku, sdílené mapy, služeb třetích stran, žijící osoba
  vidět); hlášení jen soukromě přes *Report a vulnerability* na GitHubu;
  opravy jen pro poslední vydání (`stable`).
- **Šablony úkolů** `.github/ISSUE_TEMPLATE/`: jen formuláře (*Bug*,
  *Research need*), volný úkol vypnutý, odkaz na soukromé hlášení; každý
  formulář má povinné potvrzení, že neobsahuje skutečná data rodiny (hlídá
  test).

## Důsledky

- Při přepnutí na veřejné zapnout v nastavení repa *Private vulnerability
  reporting*, jinak odkaz ze `SECURITY.md` nefunguje; založit štítky
  `bug` a `research`.
- Kontrola jmen chrání jen soubory a commity, ne text úkolů; tam pomáhá
  jen upozornění ve formuláři a smazání po nahlášení.
- Test (`tests/test_docs.py`): místní odkazy nových stránek existují,
  formuláře mají povinné potvrzení soukromí, volný úkol je vypnutý.
