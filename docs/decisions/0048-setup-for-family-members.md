# 0048 Průvodce `/proavus:setup` pro člena rodiny

- **Stav:** přijato (2026-10-21)
- **Původně:** —
- **Upřesňuje:** [ADR 0011](0011-installation-and-uv.md), [ADR 0016](0016-pilot-without-reviewers-identity-gate.md)

## Kontext

Rodinné repo zakládá `/proavus:init`, ale další člen rodiny (bez technických
znalostí) neměl jak se připojit: musel by sám nainstalovat git, `gh` a `uv`,
přihlásit se, nainstalovat plugin, naklonovat repo a zapsat se do
`repo.yaml`. ADR 0011 slibuje průvodce `/setup`. Plugin přitom nejde spustit
dřív, než je nainstalovaný, a zápis do `repo.yaml` závisí na tom, jaká práva
člen v repu má (vlastník a správce smí rovnou na `main`, spolupracovník na
osobním účtu má právo zápisu, v organizaci může mít jen čtení).

## Rozhodnutí

- **Skill `/proavus:setup`** (`skills/setup/SKILL.md`) provede člena krok po
  kroku: programy git, `gh`, `uv` (macOS: Homebrew, bez něj `xcode-select`,
  instalátor `uv` a balíček `gh`; Windows: `winget`), přihlášení `gh` přes
  prohlížeč a `gh auth setup-git`, doporučení dvoufázového ověření, plugin
  z katalogu (repo frameworku na větvi `stable`), ověření a naklonování
  soukromého rodinného repa, ochranu frameworku (`protect-plugin`), zápis
  člena do `repo.yaml` a první `/proavus:start`.
- **Každý krok nejdřív zkontroluje, jestli už je hotový**, a přeskočí ho.
  Průvodce jde proto spustit znovu po restartu aplikace (nově nainstalovaný
  program nebo plugin se často objeví až v novém sezení) i po chybě. Na
  počítači bez pluginu se poprvé spustí jako „postupuj podle
  `skills/setup/SKILL.md`“ ze staženého frameworku (README), dál jako
  `/proavus:setup`.
- **Hesla, tokeny a kódy pro obnovení nikdy v chatu.** Heslo se píše jen do
  stránky GitHubu v prohlížeči nebo do systémového okna; agent nespouští
  nic, co vypíše token (`gh auth token`, `--show-token`), a nedává token do
  příkazu, souboru ani adresy remote. Jednorázový kód přihlášení zařízení
  smí ukázat – sám o sobě nic neotevře.
- **`family_repo.py access <složka|vlastník/název>`** před klonováním
  i ukládáním zjistí soukromí a oprávnění (`gh repo view --json
  viewerPermission`): 0 = soukromé, ukládat rovnou (admin, maintain),
  2 = soukromé, přes pull request (write), 6 = jen čtení, 3 = veřejné nebo
  fork (nic nestahovat ani nezapisovat), 4 = nelze zjistit, 7 = nenalezeno
  nebo zatím bez přístupu (přijmout pozvánku).
- **`family_repo.py add-member`** přidá člena (`abbr`, `name`, `role`) na
  konec `members` a zbytek `repo.yaml` nechá, jak je napsaný (komentáře,
  pořadí). Odmítne obsazenou zkratku i druhý zápis téhož jména; stejný člen
  podruhé nic nemění.
- **Uložení podle práv:** správce a vlastník commit na `main`
  (pilot bez schvalovatelů, ADR 0016); člen s právem zápisu větev
  `member-<abbr>` a pull request, který správce sloučí – nový člen se do
  rodiny dostane s vědomím správce; jen čtení: nic se neukládá, správce musí
  přidat právo zápisu. Odmítne-li GitHub přímý push (chráněná větev), jde se
  cestou pull requestu.
- `/proavus:start` u člena, který v `repo.yaml` chybí, nejdřív hledá otevřený
  pull request `member-<abbr>`; jinak člena přidá stejným nástrojem.

## Důsledky

- Testy na fiktivním repu (`tests/test_family_repo.py`): repo vytvořené ze
  šablony a kopie fiktivní rodiny, zápis člena, validace s 0 chybami,
  odmítnutí špatných hodnot; `access` s náhradním `gh`, které vrací
  připravená data (žádný skutečný GitHub v testech).
- Diagnostika `/check` (ADR 0011) zůstává na později; jeho roli zatím
  plní opakované spuštění `/proavus:setup`.
- Dokud je framework soukromý, potřebuje člen přístup i k repu
  `proavus` (instalace pluginu z jeho klonu). Po zveřejnění (fáze 4) tato
  podmínka odpadne.
- Starší kopie `.proavus/` (do 0.4.0) `add-member` ani `access` nemají;
  skilly proto volají nástroj z pluginu (`${CLAUDE_PLUGIN_ROOT}`).
