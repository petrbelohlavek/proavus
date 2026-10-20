# Proavus – architektura

Stav: verze frameworku 0.1.0 (20. 10. 2026). Zpočátku česky, anglická verze
vznikne před zveřejněním. Rozhodnutí jsou v [`decisions/`](decisions/) (ADR);
tento dokument popisuje celek a odkazuje na ně.

Dokument vznikl rozdělením pracovního návrhu architektury (v1.22): obecná
část je zde, plán a rozhodnutí konkrétní rodiny patří do jejího soukromého
repozitáře. **Žádná data skutečné rodiny sem nepatří**; všechny příklady jsou
smyšlené.

**Cíl:** (1) veřejné repo, podle kterého může kdokoli stavět rodokmen s LLM
podle nejlepších postupů (Genealogical Proof Standard); (2) soukromé repo
každé rodiny, ve kterém její členové bádají stejným způsobem a společně tvoří
rodokmen.

---

## 1. Celkový obraz

```
FRAMEWORK (soukromý → veřejný ve fázi 4)    SOUKROMÉ REPO RODINY (private)
┌──────────────────────────┐        ┌────────────────────────────────────┐
│ proavus                  │ plugin │ proavus-<rodina>                   │
│ metodika · regiony ·     │──────► │ otázky · sezení · coverage ·       │
│ schéma dat · validátory ·│        │ přepisy · osoby · tvrzení ·        │
│ plugin · šablona repa    │ šablona│ rozpory · rodinné dokumenty · strom│
│ (kdokoli od fáze 4)      │──────► │ (jen pozvaní členové rodiny)       │
└──────────────────────────┘        └────────────────────────────────────┘
                                         ▲          ▲          ▲
                                     správce     člen A     člen B …
              (pilot: všichni zápis přímo, brána identity v sezení; cíl: badatelé fork + návrh změn)

POČÍTAČ SPRÁVCE: Proavus/ (jen složka, ne git; mimo iCloud/Dropbox/OneDrive)
  proavus/              ← git: framework (vývojová verze)
  proavus-<rodina>/     ← git: data rodiny
Mimo obě repa (jen správce): surové nahrávky a přepisy hovorů, přístupy k hostingu.
```

Rozhodnutí: dvě repa ([ADR 0001](decisions/0001-two-repositories.md)),
jádro nezávislé na modelu ([0002](decisions/0002-model-independent-core.md)),
GitHub zdarma ([0003](decisions/0003-github-free-pilot-and-target.md)).

**Tři úrovně důvěry:**

| Úroveň | Obsah | Kdo vidí |
|---|---|---|
| Veřejné (od fáze 4) | metoda, šablony, nástroje, fiktivní ukázka | kdokoli |
| Rodinné | výzkum, data zesnulých předků, rodinné paměti a dokumenty (se souhlasem), zpracované ústní výpovědi; žijící osoby jen minimálně | pozvaní členové rodiny |
| Jen správce | surové nahrávky a přepisy hovorů, přístupy k hostingu | správce |

---

## 2. Framework `proavus`

```
proavus/
├── brand/                              logo, ikona, favicon, náhled pro sociální sítě (vyhrazená práva)
├── README.md (EN) · README.cs.md       přepínač jazyků; krátká verze nahoře (5 kroků), detailní pod ní
├── docs/                               architektura, rozhodnutí (ADR), your-private-repo
├── AGENTS.md · CLAUDE.md               vstup pro agenty (CLAUDE.md jen odkazuje na AGENTS.md)
├── LICENSES/ · REUSE.toml              licence podle částí repa (kap. 9)
├── CHANGELOG.md                        jedna verze pro celé repo (ADR 0018)
│
├── method/                             JÁDRO (nezávislé na modelu i regionu)
│   ├── rules.md (+ .cs.md)             10 závazných pravidel na 1 stranu          [hotovo v 0.1.0]
│   ├── reading-records.md              doslovný přepis → výklad; druhé čtení      [hotovo v 0.1.0]
│   ├── 00-cycle.md                     otázka → plán → hledání → analýza → závěr
│   ├── evidence-model.md               zdroj/informace/důkaz, informátor, úrovně jistoty, QUAY
│   ├── coverage-and-negatives.md       registr prohledaného; negativ vs. stav přístupu
│   ├── identity.md                     kandidátní skupiny, mosty identity, FAN
│   ├── collaboration.md                více badatelů: zábor otázky, kontrola
│   └── ethics-privacy.md               žijící osoby, autorská práva, co dělá jen člověk
│
├── schema/                             DATOVÝ MODEL: JSON Schema pro záhlaví souborů (kap. 5) [v0]
│   └── vocab/                          slovníky hodnot
├── regions/                            REGIONÁLNÍ BALÍČKY (rozšiřuje komunita)
│   ├── cz/       schema-ext.yaml [v0] · pitfalls.md [v0] · sources.yaml · law.md · glossary.md · scripts.md
│   ├── at-wien/  sources.yaml · pitfalls.md
│   └── _template/
├── tools/                              Python přes `uv run` (ADR 0011, 0021); family_repo.py: init, .proavus, START-HERE, kontrola soukromí [v0]
│   ├── validate.py                     schéma, odkazy, brána identity, žijící osoby, data, negativy [v0]
│   ├── new_id.py                       ID bez kolizí                                    [v0]
│   ├── guard_names.py                  kontrola jmen rodiny před commitem frameworku     [v0]
│   ├── build_index.py · query.py       SQLite index a dotazy (fáze 3)
│   ├── build_views.py                  mapa views/mapa.html (ADR 0027–0029) [v0]; později GEDCOM
│   ├── archive_fetch.py                snímky z portálů: ARON plně, Acta Publica a Matricula jen odkaz (ADR 0041) [v0]
│   ├── bulk_import.py                  převod staršího bádání plánem (docs/import.md, ADR 0042) [v0]
│   └── migrate.py                      převod dat mezi hlavními verzemi schématu [kostra, zatím bez migrací]
├── .claude-plugin/                     PLUGIN = CELÉ REPO (ADR 0014): marketplace.json ("source": ".") · plugin.json
├── skills/                             init · start · end · upgrade [v0]; později setup · check · claim · review · feedback
├── hooks/                              kontrola před uložením v rodinném repu (později)
├── templates/family/                   ŠABLONA RODINNÉHO REPA (používá /proavus:init a /proavus:upgrade; ADR 0009) [v0]
├── adapters/chat/                      jeden prompt pro chatové nástroje bez pluginu
├── evals/                              testy napříč modely (rukopis, past rejstříku, jmenovci)
├── examples/worked-case/               fiktivní případ, bez žijících osob
└── tests/                              testy nástrojů na fiktivních datech
```

**Zásady:**
- Jedna pravda, mnoho obalů: metodika je jen v `method/`; skilly, prompty
  a plugin na ni odkazují (přes `${CLAUDE_PLUGIN_ROOT}`), nekopírují ji.
- Žádná data skutečné rodiny, žádné jméno rodiny v názvu repa; příklady
  fiktivní ([ADR 0026](decisions/0026-separating-development-from-family-data.md)).
- Odborné standardy (BCG, Mills, Jones) jen shrnuté vlastními slovy
  s odkazem; převzaté části s původní licencí a uvedením autora.
- V README poctivě: na kterých modelech je postup otestovaný a s jakým
  výsledkem evalů.

### 2.1 Název a značka

**Proavus** (lat. „praděd“, *proavi* = předkové), podtitul *Evidence-first
genealogy with AI*. Logo „otevřená matrika s rodovou linií“; barvy inkoustová
modrá `#1F3A5F`, sépie `#B8742A`, pergamen `#F6F1E7`. Podrobnosti
v [ADR 0007](decisions/0007-name-and-brand.md) a [`brand/README.md`](../brand/README.md).
Před vydáním převést nápis v logu na křivky.

### 2.2 Povinné soukromé repo a pojistky proti zveřejnění dat

**Riziko:** uživatel začne zapisovat data své rodiny do veřejného repa nebo
do jeho forku. **Fork veřejného repa je vždy veřejný** a zveřejnění je
prakticky nevratné.

**Správná cesta:** nainstalovat plugin a spustit `/proavus:init` (holé `/init` je vestavěný příkaz Claude Code, proto je příkaz pluginu s předponou). Příkaz založí nové
**soukromé** repo `proavus-<rodina>` (výchozí `proavus-family`), naplní ho
šablonou a ověří, že je soukromé. Fork `proavus` slouží jen k příspěvkům do
metody.

| Místo | Obsah |
|---|---|
| README (EN + CS), rychlý start | „Založ si soukromé repo příkazem `/init`“; varování před daty ve forku |
| `docs/your-private-repo.md` (+ CS) | proč dvě repa; co kam patří; založení; pozvání rodiny; co při úniku |
| `method/ethics-privacy.md` | data rodiny jen v soukromém úložišti, žijící osoby minimálně |
| `templates/family/README.md` | první kroky po založení; kontrola, že repo je soukromé |

**Strojové pojistky:** `/start` odmítne zapisovat do veřejného repa nebo
forku `proavus`; hook před uložením a `validate.py` zablokují zápis dat, pokud
vzdálené repo není soukromé; kontrola ve frameworku odmítne soubory dat rodiny
(výjimkou je fiktivní ukázka).

### 2.3 README a jazykové verze

README (EN i CS) má **krátkou verzi** nahoře (jedna věta + 5 kroků:
účet a aplikace → „Nastav mi Proavus podle …“ → `/start` → popsat, koho
hledám → `/end`) a **detailní verzi** pod ní (co je Proavus, jak funguje,
instalace, sezení, práce s rodinou, ochrana dat, regiony, ověřené modely,
přispívání a licence).

Jazyky: jeden soubor na jazyk s příponou (`README.cs.md`, `rules.cs.md`)
a přepínačem na prvním řádku; vlajky jako malé SVG spolu s názvem jazyka
(Windows vlajková emoji nezobrazuje). Angličtina je zdrojová verze metodiky,
překlad nese v záhlaví verzi zdroje (`<!-- source: … @ v0.1.0 -->`);
kontrola upozorní, když je překlad pozadu. Příkazy, názvy souborů a pole
schématu jsou anglicky; agent odpovídá v jazyce uživatele. Regionální balíčky
v jazyce regionu s krátkým anglickým souhrnem.

---

## 3. Soukromé repo rodiny (šablona)

```
proavus-<rodina>/
├── CLAUDE.md · AGENTS.md            pravidla rodiny + vyžadovaná verze pluginu (blok proavus:begin/end spravuje /upgrade)
├── README.md                        návod pro nové členy (1 strana)
├── START-HERE.md                    GENEROVANÉ lokálně při /start, není v gitu (ADR 0019)
├── repo.yaml                        schema_version, regiony a rozšíření, členové (zkratky), práh žijících, nastavení mapy (map.root, map.lang, map.living_places)
├── lines.yaml                       linie rodiny
├── .proavus/                        KOPIE nástrojů, schématu a slovníků, připnutá na verzi (spravuje /upgrade; ADR 0014)
│
├── questions/                       1 otázka = 1 soubor
├── sessions/YYYY/                   1 sezení = 1 soubor
├── coverage/                        registr prohledaného: 1 prohledání zdroje = 1 soubor
├── records/                         přepisy zápisů s účastníky; čteno 1× / potvrzeno
│   └── evidence/                    jen výřezy (malé JPEG)
├── people/ · relationships/ · assertions/
├── conflicts/ · places/ · sources/ · oral/ · decisions/
├── inquiries/                       dotazy na úřady, archivy a fary se stavem (ADR 0036)
├── chronicle/                       KRONIKA VÝZKUMU: 1 milník = 1 soubor (ADR 0020)
├── archive/                         zmrazené podklady z doby před přechodem
├── views/                           GENEROVANÉ na požádání, není v gitu: mapa, GEDCOM, history.md
└── .github/workflows/               validate (jen kontroluje, nic nezapisuje)
```

**Formát:** Markdown se záhlavím YAML, 1 entita = 1 soubor; názvy souborů
ASCII, obsah v jazyce rodiny. **ID bez kolizí:**
`<typ>-<YYYYMMDD>-<zkratka člena>-<3 znaky>`, např. `Q-20261019-jn-k7m`
([ADR 0024](decisions/0024-collision-free-ids.md)).

**Záznam o průběhu výzkumu:**

| Vrstva | Kde | Co zachycuje |
|---|---|---|
| Deník výzkumu | `sessions/` | co se hledalo, kde, výsledek, další krok |
| Prohledané zdroje | `coverage/` | knihy a rozsahy, varianty jmen, negativy |
| Rozhodnutí | `decisions/` | proč se co rozhodlo, souhlasy |
| Závěry otázek | `questions/` | zdůvodnění závěru (GPS) |
| Kronika | `chronicle/` | milníky jako čitelný příběh včetně slepých uliček |
| Historie gitu | automaticky | kdo co kdy změnil |

---

## 4. Role, přístup a průběh práce

**Cílový stav** (organizace rodiny na GitHubu): vlastníci (2 kvůli
kontinuitě), schvalovatelé (zápis, druhé čtení, sloučení návrhů), badatelé
(jen čtení + soukromý fork, návrhy změn), volitelně garanti linií. GitHub Free
u soukromých rep nevynutí ochranu větve, proto ochranu zajišťují oprávnění
(model forků).

**Pilot** (osobní účet, 2–3 důvěryhodní členové; [ADR 0016](decisions/0016-pilot-without-reviewers-identity-gate.md)):
všichni mají zápis; **bez schvalovatelů a bez návrhů změn** – Claude zapisuje
přímo do hlavní větve (před uložením stáhne novinky); hlídá stroj a Claude;
**člověk jen u brány identity**, a to sám badatel v sezení.

**Jedno sezení:** `/start` (stáhne novinky, vygeneruje START-HERE, přečte
otázku a coverage) → `/claim Q-…` (zábor otázky) → bádání podle metodiky
→ `/end` (validátor, uložení, další krok) → volitelně `/review` (přehled „co
přibylo“).

**Kdy přejít z pilotu na cílový stav:** člen, který nemá být schvalovatelem;
víc než ~3–4 aktivní badatelé; chyby z přímých zápisů; potřeba druhého
vlastníka. Převod repa do organizace zachová historii i odkazy.

---

## 5. Datová a technická vrstva

```
Markdown + YAML (zdroj pravdy, v gitu)
      │  tools/build_index.py
      ▼
SQLite (lokální, odvozený, není v gitu): dotazy · fulltext · fonetika
      │  tools/build_views.py
      ▼
START-HERE.md · views/mapa.html · rodokmen.ged  (lokálně, ne v gitu)  →  případně import do webtrees
```

| Prvek | Standard | Přínos |
|---|---|---|
| Datový model | tvrzení → závěry o osobách, podle GPS a GEDCOM X | závěr stojí na doložených tvrzeních |
| Schéma souborů | JSON Schema (draft 2020-12) | neúplný záznam neprojde |
| Nejistá data | podmnožina EDTF | `1935?`, `1904/1906`; kontrola časových nesmyslů |
| Varianty jmen | Daitch-Mokotoff / Beider-Morse (fáze 3) | Novák = Nowak = Nowack jedním dotazem |
| Místa | ID z GOV + historické a jazykové varianty | jednoznačné farnosti |
| Fulltext | SQLite FTS5 (fáze 3) | hledání v přepisech a dokumentech |
| Export | GEDCOM 5.5.1, později 7, s QUAY | strom bez ruční práce |

**Proč ne databázový server:** databázi nejde slučovat ani kontrolovat přes
git, chybí historie změn, potřebuje provoz a nevydrží desítky let bez
software ([ADR 0004](decisions/0004-markdown-yaml-source-of-truth.md)).

**Co je v gitu:** entity jako Markdown + YAML; přepisy zápisů; výřezy snímků
(JPEG ~300 kB); rodinné dokumenty jako originál + textová verze; konfigurace
(`repo.yaml`, `lines.yaml`). **Generované, ne v gitu:** START-HERE, mapa,
GEDCOM, index ([ADR 0019](decisions/0019-generated-outputs-not-in-git.md)).
**Do gitu nepatří:** surové nahrávky a přepisy hovorů, hesla a přístupy,
citlivé údaje o žijících nad minimum, skeny celých knih.

**Šifrování:** soukromé repo na GitHubu není šifrované před GitHubem.
Šifrování vybraných souborů by rodině přidalo složitost; protože o žijících
ukládáme jen minimum, nešifruje se a citlivé údaje do repa nepatří.

### 5.1 Schéma v0

Podrobně v [`schema/README.md`](../schema/README.md). Klíčové body:

- 14 typů entit (9 úplně, 5 minimálně; od 0.3 `inquiry`); fakta jako tvrzení s typem
  ([ADR 0015](decisions/0015-extensible-schema.md));
- **účastník zápisu není osoba**; propojení je tvrzení o identitě
  ([ADR 0017](decisions/0017-record-participants.md));
- dvě osy: forma zdroje + informace + důkaz u citace, jistota u závěru; QUAY
  se odvozuje ([ADR 0022](decisions/0022-evidence-axes-and-confidence.md));
- citace s povinným lokátorem ([ADR 0023](decisions/0023-citation-locator.md));
- žijící osoby ([ADR 0025](decisions/0025-living-persons.md));
- schéma 0.3: více výřezů a poznámky na okraji u zápisu, čtení agentem a
  člověkem, více mluvčích, hledání dotazem, dotazy na úřady, úkoly se stavem,
  citace u vztahu (ADR 0031–0038); migrace i v menších verzích (ADR 0030).

| Vrstva | Obsah | Jak se mění |
|---|---|---|
| 1. Pevné jádro | entity, ID, odkazy, tvrzení, účastníci, jistota, lokátor | přidání = menší verze (smí mít sjednocující migraci, ADR 0030); zásadní změna = hlavní verze + `migrate.py` |
| 2. Slovníky | typy událostí a faktů, typy jmen, role, podtypy vztahů, vyznání… | přidáním hodnoty (menší verze) |
| 3. Regionální rozšíření | `regions/cz/schema-ext.yaml` (číslo popisné, panství) | zapne rodina v `repo.yaml` |
| 4. Záchranná síť | `schema_gap:` u věci, kterou schéma neumí | kdykoli; výzkum se nezastaví |

**Cesta nového případu:** `schema_gap` při bádání → `/feedback` bez dat
rodiny → rozhodnutí (ADR) → nová verze → `/upgrade` nabídne převést dosavadní
poznámky.

### 5.2 Zvažované technologie

| Technologie | Proč ne jako zdroj pravdy |
|---|---|
| **Markdown + YAML v gitu** | **zvoleno** |
| JSON/YAML bez Markdownu | dlouhé přepisy se špatně čtou a píšou |
| GEDCOM jako hlavní soubor | jeden soubor = konflikt při každé změně; slabý model důkazů |
| GEDCOM X | malá podpora v programech |
| SQLite v gitu | binární: bez rozdílů a slučování |
| Serverová / grafová databáze | provoz, zabezpečení, bez kontroly změn |
| Gramps / Gramps Web | data v databázi programu, LLM jen přes API |
| webtrees | vhodné jen jako publikační vrstva (dva zdroje pravdy) |
| Online stromy (placené služby) | závislost na dodavateli; LLM bez přímého přístupu |
| Obsidian | jen prohlížeč stejných souborů (volitelně) |
| Notion, tabulky | slabá kontrola změn a model důkazů |

---

## 6. Princip práce: stroj → LLM → člověk

[ADR 0005](decisions/0005-machine-llm-human.md). Každé pravidlo metodiky se při
stavbě posoudí: jde převést na kontrolu ve validátoru? Pokud ano, převést;
text v `method/` pak vysvětluje proč.

| Krok | Stroj | LLM | Člověk |
|---|---|---|---|
| ID, soubor ze šablony | ✔ | | |
| Otázka a plán | kontrola polí | ✔ návrh | schválí |
| Výběr zdroje | ✔ katalog podle místa a období | ✔ pořadí | |
| „Už to někdo hledal?“ | ✔ dotaz do `coverage/` | | |
| Varianty jmen | ✔ fonetika + pravidla | ✔ neobvyklé podoby | |
| Přepočet strana ↔ folio | ✔ z kalibračních bodů | ✔ ovládá prohlížeč | přihlášení do portálů |
| Čtení rukopisu | | ✔ první čtení, nejistoty v [ ] | ✔ druhé čtení u identity |
| Negativ | ✔ kontrola rozsahu a variant | ✔ popis | |
| Časové nesmysly, chybějící vazby | ✔ validátor | | |
| Rozpory a hypotézy | ✔ detekce | ✔ analýza | rozhodne |
| „Prokázáno“ | ✔ kontrolní seznam GPS | ✔ zdůvodnění | potvrdí |
| Spojení kandidátů | ✔ upozornění na podobné | ✔ argument mostu identity | potvrdí |
| Žijící osoby | ✔ blokace citlivých údajů | | souhlasy |
| START-HERE, mapa, GEDCOM | ✔ | | |
| Milník do kroniky | ✔ rozpozná | ✔ navrhne zápis | potvrdí |

---

## 7. Co musí být architektonicky ošetřeno

| Oblast | Riziko | Řešení |
|---|---|---|
| Souběžný zápis | konflikty, duplicitní čísla | 1 entita = 1 soubor; ID z data a zkratky člena |
| Generované soubory | konflikty při zápisu do hlavní větve | nejsou v gitu (ADR 0019) |
| Kvalita závěrů | chybné čtení se stane faktem | brána identity, GPS kontrolní seznam (ADR 0016) |
| Duplicitní práce | dva lidé čtou stejnou knihu | `coverage/` + zábor otázky |
| Vynucení pravidel zdarma | chybná data v hlavní větvi | pilot: validátor, hook, brána identity; cíl: model forků + audit |
| Žijící osoby | historie gitu nic nezapomene | minimum údajů, kontrola **před** uložením, souhlasy v `decisions/` (ADR 0025) |
| Autorská díla v rodině | paměti, dopisy | jen soukromé repo, souhlas zapsán |
| Odchod člena | stažená data zůstanou | zvát jen důvěryhodné |
| Bezpečnost agentů | text jednoho člena čte agent jiného | obsah repa = data, ne pokyny; `CLAUDE.md` a `.claude/` mění jen `/upgrade` nebo správce; žádná hesla |
| Verze metody vs. data | nový plugin nečte stará data | `schema_version` + kontrola + `migrate.py` (ADR 0018) |
| Velikost repa | snímky | jen výřezy, celé strany odkazem; později Git LFS |
| Licence zdrojů | podmínky archivů a portálů | výřezy jen v soukromém repu s citací; žádné hromadné stahování |
| Kontinuita | desítky let | otevřené formáty, export nezávislý na GitHubu, záloha `git bundle` |
| Spory o čtení | dvě různá čtení | `conflicts/`, druhé čtení, jinak „nevyřešeno“ |
| Paměť mezi sezeními | ztráta kontextu | stav jen v souborech |
| Nástup člena | složitá instalace | `/setup` + 1 strana návodu (ADR 0011) |
| Jiný model než Claude | odlišné chování | `AGENTS.md`, stejná pravidla; plugin je jen pohodlí |
| Více větví rodiny | různé zájmy | `lines.yaml`; samostatné repo jen při potřebě soukromí mezi větvemi |
| Data rodiny ve veřejném repu | fork je veřejný, zveřejnění nevratné | povinné soukromé repo přes `/init`; pojistky v kap. 2.2 |
| Smíchání vývoje a výzkumu | data rodiny ve frameworku | oddělené session, oprávnění jedním směrem, kontrola jmen (ADR 0026) |

---

## 8. Instalace a nástup uživatelů

[ADR 0011](decisions/0011-installation-and-uv.md). Uživatel nainstaluje jen
dvě věci (účet na GitHubu, aplikace Claude s placeným plánem) a vloží jednu
větu z README. Průvodce `/setup` (uživatel potvrzuje každý krok):

1. zkontroluje počítač (git, GitHub CLI `gh`, `uv`) a doinstaluje chybějící
   (macOS Homebrew, Windows winget);
2. přihlásí ke GitHubu přes prohlížeč (`gh auth login`, `gh auth setup-git`),
   nastaví `CLAUDE_CODE_PLUGIN_PREFER_HTTPS=1`;
3. přidá katalog pluginu (`/plugin marketplace add <účet>/proavus#stable`),
   nainstaluje plugin a provede zapnutím automatických aktualizací;
4. založí soukromé repo (`/init`) nebo stáhne rodinné repo, kam byl pozván;
5. „Vše připraveno, napište `/start`.“

`/check` kdykoli vyhodnotí, co nefunguje. Při běžné práci git uživatel nevidí.

**Pojistky pro Windows:** hooky a skripty v Pythonu, ne v Bashi;
`.gitattributes` kvůli koncům řádků; názvy souborů jen ASCII.

**Úrovně zapojení:** *badatel* (aplikace + `/setup`, plný postup) a
*pomocník* (nic neinstaluje; posílá vzpomínky, fotky a jména badateli).

---

## 9. Licence

[ADR 0012](decisions/0012-licences-by-part.md); označení podle standardu REUSE
(`REUSE.toml`, plné texty v `LICENSES/`).

| Část repa | Licence |
|---|---|
| Metodika a dokumentace (`method/`, `docs/`, `regions/`, README) | CC BY 4.0 |
| Kód (`tools/`, `tests/`, hooky, workflow) | MIT |
| Schéma, slovníky, regionální rozšíření schématu, šablona rodinného repa, manifest pluginu, drobná konfigurace | CC0 1.0 |
| Název a logo (`brand/`) | všechna práva vyhrazena (`LicenseRef-Proavus-Brand`) |
| Převzaté části | původní licence |

Data rodiny licenci nemají – jsou soukromá. Příspěvky přicházejí pod licencí
dané složky („co přijde, to odejde“).

---

## 10. Vývoj frameworku a vlastního rodokmenu

[ADR 0013](decisions/0013-research-driven-development.md),
[ADR 0026](decisions/0026-separating-development-from-family-data.md).

**Princip:** vývoj řízený vlastním výzkumem. Framework je nástroj s verzemi,
rodinné repo ho jen používá a nikdy ho do sebe nekopíruje (kromě připnuté
kopie nástrojů v `.proavus/`). Správce vylepšuje nástroj a zkouší ho na
vlastních datech dřív, než ho dostane rodina.

**Dvě session v Claude Code:**

| Session | Pracovní složka | Přístup k druhému repu |
|---|---|---|
| Výzkum | `Proavus/proavus-<rodina>` | `Proavus/proavus` jen ke čtení a spouštění |
| Framework | `Proavus/proavus` | **žádný** (zákaz čtení v `.claude/settings.local.json`) |

Celé `Proavus/` se jako jedna pracovní složka neotevírá.

**Vývojová smyčka:** nedostatek při bádání (chybí pole, validátor chybu
nepoznal) → oprava ve frameworku → hned vyzkoušet na vlastních datech →
vydání verze → rodině se aktualizuje plugin.

1. **Nástroje:** správce je spouští z lokální kopie frameworku, rodina
   z pluginu, automatická kontrola na GitHubu z `.proavus/`.
2. **Dva kanály pluginu:** správce z lokálního katalogu `../proavus`
   (změny po `/reload-plugins`), rodina z větve `stable` (posouvá se při
   vydání, zvyšuje se `version` v `plugin.json`).
3. **Data rodiny jsou integrační test:** před vydáním testy frameworku +
   validace celého rodinného repa novou verzí.
4. **Každá změna má důvod ve výzkumu.** Žádné funkce do zásoby.
5. **Vydávání po dávkách** se záznamem v `CHANGELOG.md`.

**Soubory frameworku vs. soubory rodiny:**

| Patří frameworku (mění jen `/upgrade`) | Patří rodině (framework nikdy nemění) |
|---|---|
| blok `<!-- proavus:begin -->` … `<!-- proavus:end -->` v `CLAUDE.md` a `AGENTS.md` | zbytek `CLAUDE.md`, rodinná pravidla |
| `.github/workflows/` (jen validace) | všechny datové složky (`questions/` … `archive/`) |
| `schema_version` v `repo.yaml` | ostatní pole `repo.yaml`, `lines.yaml` |
| `.proavus/` | — |
| `.gitignore` pro generované výstupy | — |

**Zpětná vazba bez dat:** `/feedback` připraví popis nedostatku bez jmen
a údajů rodiny. Seznam jmen rodiny je v souboru mimo obě repa
(`Proavus/.guard-names`); používá ho hook `tools/guard_names.py` ve frameworku.
Z reálných problémů vznikají fiktivní testovací případy.

---

## 11. Fáze

| Fáze | Obsah | Výsledek |
|---|---|---|
| 1. MVP | obě repa soukromá; schéma v0, `rules.md`, `reading-records.md`, `validate.py` s testy, plugin (`/init`, `/start`, `/end`, `/review`); převod jedné otázky | správce bádá v novém modelu |
| 2. Pilot | převod dat, návod pro členy, 2–3 členové | pilot běží |
| 3. Kvalita | podle potřeb pilotu: SQLite index, fonetika, GOV, `/upgrade`, `/feedback`, evaly | strojové kontroly, ověřená metoda |
| 4. Veřejnost | zveřejnění metody, fiktivní ukázka, `AGENTS.md`, chatový adaptér, příspěvky | veřejné repo |
| 5. Vlastní git server | Forgejo/Gitea: účty bez GitHubu, vynucené schvalování | rodiny mimo GitHub |
| 6. Genealogická služba | API + MCP: sdílený registr prohledaného, shoda předků, katalog | síťový efekt |

**Pořadí stavby MVP:** (1) založit obě repa jako soukromá → (2) framework
minimum: schéma v0, metodika, `validate.py`, rozdělení návrhu do `docs/`
→ (2b) `/init`, `/start`, `/end` → (3) `/init` vytvoří kostru rodinného repa
→ (4) převést jednu otázku → (5) pokračovat ve výzkumu, framework doplňovat
→ (6) převést zbytek → (7) vydat první verzi, přizvat rodinu → (8) přepnout
`proavus` na veřejné.

**Před zveřejněním (fáze 4):** prohledat celou historii na data rodiny
a hesla (nástroj na tajné klíče + kontrola jmen); projít issues a komentáře;
smazat nepotřebné větve; při sporné historii raději nové repo s čistou
historií; veřejná výbava (CONTRIBUTING, pravidla chování, `SECURITY.md`,
šablony úkolů, evaly, fiktivní ukázka, nápis loga na křivky, formální ověření
známky); rozhodnout o spolupracovnících z pilotu.

---

## 12. Vlastní úložiště a sdílení mezi rodinami (fáze 5–6)

[ADR 0006](decisions/0006-own-storage-later.md) (navrženo). Každá rodina bádá
sama přes vlastní LLM; soukromá data se ukládají do úložiště, které zvládne
neomezený počet rodin. Výzkum, čtení snímků a náklady na LLM zůstávají
u uživatele; server nikdy nepřistupuje k archivům ani nevolá LLM.

| Přínos | GitHub zdarma | Vlastní úložiště |
|---|---|---|
| Účet bez GitHubu | ne | ano |
| Vynucená kontrola změn | ne (jen model forků) | ano |
| Oprávnění na části dat, filtr žijících | ne | ano |
| Sdílení mezi rodinami | ne | ano (hlavní hodnota) |

**Sdílení (jen zemřelé osoby, jen se souhlasem):** společný registr
prohledaného, shoda předků mezi rody, sdílený katalog zdrojů a míst.

**Ošetřit:** ochranu osobních údajů (role zpracovatele, hosting v EU,
právní posouzení údajů o zemřelých), zabezpečení, local-first kontinuitu
(úplná lokální kopie, export kdykoli), synchronizaci, přístup agentů (git,
později MCP), výslovný souhlas se sdílením, model financování.

**Klíčová podmínka:** datový formát je od začátku stejný pro GitHub, vlastní
server i službu; každý krok mění jen to, kde data leží.

**Zamítnuto:** plná cloudová služba, ve které server sám volá LLM a čte
archivy (náklady, podmínky archivů, ztráta výhod gitu, provoz).

---

## 13. Otevřené body frameworku

1. Ověřit na github.com minutáž Actions pro soukromá repa; pro cílový stav
   ochranu větví a forkování soukromých rep v organizaci.
2. Ověřit podporu `SKILL.md` a `AGENTS.md` v dalších nástrojích.
3. Ověřit licence převzatých skillů před převzetím čehokoli.
4. Formální ověření ochranné známky Proavus před zveřejněním.
5. Ztrátový převod do GEDCOMu: popsat, co se z modelu důkazů nepřenese.
6. Podmínky archivů a portálů pro výřezy (ověřit u každého zdroje).
7. Vlastní úložiště: chráněné větve ve Forgejo/Gitea, hosting, právní
   posouzení, financování.

---

## Zdroje

- Standardy: BCG Genealogy Standards (2. vyd.), Genealogical Proof Standard,
  E. S. Mills: *Evidence Explained*, T. W. Jones: *Mastering Genealogical
  Proof* (shrnuto vlastními slovy).
- Formáty: JSON Schema 2020-12, EDTF (ISO 8601-2), GEDCOM 5.5.1 / 7, GEDCOM X,
  GOV (gov.genealogy.net), REUSE 3.3.
- Existující skilly a projekty pro genealogii s LLM (analýza před návrhem;
  licence ověřit před převzetím).
