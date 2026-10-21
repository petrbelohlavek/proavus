<!-- source: README.md @ v0.5.0 -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/proavus-logo-dark.svg">
    <img src="brand/proavus-logo.svg" alt="Proavus" width="360">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <b>Čeština</b></p>

**Proavus** – rodokmen s AI podle důkazů, ne odhadů: metodika, datové schéma
a nástroje pro bádání s LLM podle Genealogical Proof Standardu.

> **Rozpracováno (0.4.0).** Existuje schéma, validátor, závazná pravidla
> a příkazy (`/proavus:init`, `/proavus:setup`, `/proavus:start`,
> `/proavus:end`, `/proavus:upgrade`). Zatím není k běžnému použití.

## Jak to bude fungovat

1. Založte si účet na GitHubu a nainstalujte desktopovou aplikaci Claude.
2. Požádejte Clauda o nastavení Proavus – vše doinstaluje a založí vám vlastní
   **soukromé** repo rodiny. Nikdy nezapisujte data rodiny do forku Proavus:
   forky jsou veřejné.
3. Otevřete své soukromé repo a napište `/proavus:start`.
4. Popište, koho hledáte; Claude s vámi sestaví otázku a plán a provede vás
   čtením zápisů.
5. Napište `/proavus:end`: výsledky se uloží s citacemi zdrojů a zkontrolují.

## Instalace pluginu z místní složky

Dokud Proavus není veřejný, instaluje se plugin z místní kopie tohoto repa:
repo je samo sobě katalogem pluginů (`.claude-plugin/marketplace.json`,
plugin je celé repo, ADR 0014). Je potřeba Claude Code 2.1.275 nebo novější
(`claude --version`). Desktopová aplikace (karta Code) i příkaz `claude`
v terminálu sdílejí stejné nastavení, takže stačí nainstalovat jednou na
počítač – v terminálu.

**Claude Code instaluje to, co je v té složce právě checkoutnuté.** Používejte
větev `stable` – poslední vydání. `main` je rozpracovaný (jen pro vývoj
Proavus).

1. **Stáhněte framework** (větev `stable`) do složky mimo iCloud Drive,
   Dropbox, OneDrive nebo Google Drive, např.
   `git clone --branch stable https://github.com/petrbelohlavek/proavus.git ~/Documents/Proavus/proavus`
   (zatím soukromé – potřebujete přístup).
2. **Přidejte katalog a nainstalujte plugin:**
   ```
   claude plugin marketplace add ~/Documents/Proavus/proavus
   claude plugin install proavus@proavus
   ```
3. **Zkontrolujte, co je nainstalované.** `claude plugin list` a `claude
   plugin details` čtou složku frameworku, ne nainstalovanou kopii – ukazují
   verzi složky, i když je nainstalovaná starší. Nainstalovanou verzi a commit
   má Claude Code ve vlastním seznamu:
   ```
   python3 -c "import json,os; e=json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))['plugins']['proavus@proavus'][0]; print(e['version'], e['gitCommitSha'][:7])"
   git -C ~/Documents/Proavus/proavus log -1 --format=%h
   ```
   Oba řádky musí ukázat stejný commit (a verzi podle `CHANGELOG.md`).
4. **Zkontrolujte příkazy v sezení** – to rozhoduje. Sezení spuštěná před
   instalací plugin nevidí – restartujte desktopovou aplikaci nebo začněte
   nové sezení:
   - **terminál:** spusťte `claude` v libovolné složce a napište `/proavus:` –
     nabídka ukáže `/proavus:init`, `/proavus:setup`,
     `/proavus:start`, `/proavus:end` a `/proavus:upgrade`;
   - **desktopová aplikace:** otevřete nové sezení na kartě Code a do pole
     zprávy napište `/proavus:` – objeví se stejných pět příkazů.

   Rychlá kontrola, která nic nemění: v prázdné složce spusťte
   `claude -p "/proavus:start" --permission-mode plan` – Proavus odpoví, že
   složka zatím není repo rodiny, a nabídne `/proavus:init`.
5. **Založte repo rodiny** příkazem `/proavus:init` (v novém sezení ve
   složce, kde má být). Ten také zakáže nástrojům Claude Code pro úpravu
   souborů sahat z repa rodiny do složky frameworku (tamní
   `.claude/settings.local.json`).

## Připojení člena rodiny (`/proavus:setup`)

Správce pozve člena do soukromého repa rodiny (GitHub → repo → Settings →
Collaborators) a dokud je Proavus soukromý, také do
`petrbelohlavek/proavus`. Člen si založí účet na GitHubu, nainstaluje
desktopovou aplikaci Claude a v novém sezení na kartě Code (v libovolné
složce, např. Dokumenty) napíše:

> Nastav mi Proavus: nainstaluj git a GitHub CLI, přihlas mě ke GitHubu přes
> prohlížeč, stáhni https://github.com/petrbelohlavek/proavus (větev
> `stable`) do `Documents/Proavus/proavus` a postupuj podle
> `skills/setup/SKILL.md` v něm. Moje rodinné repo je
> `<vlastník>/proavus-<rodina>`.

Na počítači, kde už plugin je, stačí `/proavus:setup`. Průvodce se ptá před
každým krokem a hotové kroky přeskočí, takže ho jde po restartu spustit
znovu:

1. git, `gh` a `uv` (macOS: Homebrew, nebo instalátory systému; Windows:
   `winget`);
2. přihlášení ke GitHubu v prohlížeči (`gh auth login --web`,
   `gh auth setup-git`) a doporučení zapnout dvoufázové ověření;
3. plugin z katalogu (větev `stable`, jako výše);
4. ověří, že repo rodiny je soukromé a co smí účet dělat
   (`tools/family_repo.py access`), a naklonuje ho;
5. zapíše člena do `repo.yaml` – zkratku, jméno a roli (badatel, pomocník,
   správce) – commitem (admin, maintain) nebo pull requestem pro správce
   (write);
6. předá na `/proavus:start` ve složce rodiny.

Každý commit v repu rodiny se nejdřív zkontroluje: `.githooks/pre-commit`
spustí validátor na to, co se ukládá, a commit s chybou zastaví (ADR 0049);
`/proavus:setup`, `/proavus:start` a `/proavus:upgrade` ho zapnou v každém
klonu.

**Heslo, token ani kód pro obnovení nikdy nepište do chatu** – heslo patří
jen do stránky GitHubu v prohlížeči nebo do systémového okna.

**Aktualizace na nové vydání:**
```
git -C ~/Documents/Proavus/proavus pull
claude plugin marketplace update proavus
claude plugin uninstall proavus@proavus
claude plugin install proavus@proavus
```
potom kontrola jako v kroku 3 a restart desktopové aplikace (nebo nové
sezení); v každém repu rodiny pak `/proavus:upgrade`.
Samotné `claude plugin update proavus@proavus` nestačí: nainstaluje jen
**nové číslo verze** a při změně obsahu pod stejným číslem hlásí „already at
the latest version“ – nová instalace vezme vždy to, co je ve složce.

**Odebrání:** `claude plugin uninstall proavus@proavus` a
`claude plugin marketplace remove proavus`.

Nástroje běží přímo z této složky (`${CLAUDE_PLUGIN_ROOT}` je sama složka)
a Claude Code ji navíc kopíruje – i se soubory, které git ignoruje – do své
mezipaměti pluginů. Ve složce frameworku nemějte nic soukromého.

## Používání příkazů

Příkazy se píšou do pole zprávy v sezení Claude Code (desktopová aplikace
nebo `claude` v terminálu): napište `/proavus:` a vyberte. Rozhoduje,
**ve které složce sezení běží** – je vidět pod polem zprávy.

| Příkaz | Kdy | Kde | Co dělá |
|---|---|---|---|
| `/proavus:init` | jednou | nové sezení ve složce, kde má repo rodiny vzniknout, nebo v jeho prázdném klonu | založí **soukromé** repo rodiny ze šablony, nainstaluje `.proavus/`, ochrání framework před úpravami, zapne kontrolu před každým commitem, nahraje repo na GitHub a ověří, že je soukromé |
| `/proavus:setup` | jednou na počítač a člena | nové sezení v libovolné složce (ne ve frameworku) | nainstaluje git, gh, uv a plugin, přihlásí ke GitHubu, naklonuje soukromé repo rodiny, zapíše člena do `repo.yaml` (commit nebo pull request), doporučí dvoufázové ověření |
| `/proavus:start` | první zpráva každého sezení bádání | sezení v repu rodiny | kontrola soukromí, stažení práce ostatních, přehled (`START-HERE.md`), výběr nebo zápis výzkumné otázky |
| `/proavus:end` | poslední zpráva každého sezení bádání | totéž sezení | záznam sezení s dalším krokem, rozhodnutí, která dělá jen člověk, validace (0 chyb), uložení na GitHub |
| `/proavus:upgrade` | když `/proavus:start` hlásí, že kopie Proavus je starší než plugin | sezení v repu rodiny, bez neuložených změn | ukáže, co se změní, zeptá se na nová nastavení (např. výchozí osobu mapy), aktualizuje `.proavus/`, bloky Proavus, kontrolní workflow a `schema_version`, při potřebě převede data, zvaliduje a uloží |

Nikdy ve složce frameworku `proavus`: `/proavus:start` a `/proavus:end` se
tam zastaví, `/proavus:init` odmítne složku, která není prázdná. Zapomněli
jste? `/proavus:start` jde spustit kdykoli; po vynechaném `/proavus:end`
otevřete sezení ve složce rodiny a spusťte ho – práce je pořád v souborech,
jen ještě není uložená. Podrobnosti pro členy rodiny jsou v README repa
rodiny.

## Mapa rodiny

`tools/build_views.py` vytvoří z repa rodiny jednu soběstačnou stránku HTML:
funguje offline, nic nenačítá z internetu a do gitu se neukládá. Ukázka je
z fiktivní testovací rodiny v `tests/fixtures/family/`. Barva karty ukazuje,
jak je osoba doložená, čára, jak jistý je vztah.

<p align="center"><img src="docs/images/map-tree.cs.png" alt="Mapa rodiny: strom předků ve sloupcích generací, karty obarvené podle doložení a čáry podle jistoty" width="800"></p>

Kliknutím na kartu se otevře detail se všemi údaji, jejich jistotou a zdrojem:

<p align="center"><img src="docs/images/map-detail.cs.png" alt="Detail osoby: údaje se zdroji, vztahy, otevřený rozpor a otázka" width="700"></p>

## Co tu je

| Část | Kde |
|---|---|
| Deset závazných pravidel | [method/rules.cs.md](method/rules.cs.md) |
| Čtení zápisů | [method/reading-records.md](method/reading-records.md) (anglicky) |
| Datové schéma v0 | [schema/](schema/README.md) |
| Validátor | `uv run tools/validate.py <repo-rodiny>` |
| Mapa rodiny | `uv run tools/build_views.py <repo-rodiny>` → `views/mapa.html` |
| Převod staršího bádání | [docs/import.cs.md](docs/import.cs.md) – `uv run tools/bulk_import.py plan.yaml --dry-run`, příklad v [examples/import/](examples/import/) |
| Snímky z archivů | `uv run tools/archive_fetch.py list <odkaz na knihu>` (ARON; Acta Publica a Matricula jen odkazy, ADR 0041) |
| Architektura a rozhodnutí | [docs/architecture.md](docs/architecture.md), [docs/decisions/](docs/decisions/) |

## Licence

| Část | Licence |
|---|---|
| Metodika a dokumentace (`method/`, `docs/`, `regions/`, README) | CC BY 4.0 |
| Kód (`tools/`, `tests/`, hooky, workflow) | MIT |
| Schéma, slovníky, šablona repa rodiny | CC0 1.0 |
| Název a logo (`brand/`) | všechna práva vyhrazena |

Podrobnosti v [`REUSE.toml`](REUSE.toml) a [`LICENSES/`](LICENSES/).
© 2026 Petr Bělohlávek a přispěvatelé Proavus.
