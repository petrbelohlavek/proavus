# 0050 Regionální balíček `at` a katalog portálů v `regions/*/portals.yaml`

- **Stav:** přijato (2026-10-21)
- **Původně:** —
- **Upřesňuje:** [ADR 0015](0015-extensible-schema.md), [ADR 0041](0041-archive-portals.md)

## Kontext

Pilot vedl výzkum z českých matrik do Vídně (Matricula Online, hřbitovy
města, WStLA, ANNO, adresáře). Vídeňské zkušenosti neměly kam patřit:
`regions/cz/pitfalls.md` je o českých zemích a návrh architektury počítal
s balíčkem `at-wien/` se `sources.yaml`. Zkušenosti s portály (co agent smí,
co portál neumí, jak správně citovat) byly roztroušené v tabulce
v `pitfalls.md` a v kódu `archive_fetch.py`; pro portály bez adaptéru
nástroj hlásil jen „unknown portal“.

## Rozhodnutí

- **Balíček `regions/at/`** (Rakousko; Vídeň uvnitř, ne zvláštní balíček –
  stejná zrnitost jako `cz`, zákony a portály jsou zemské i celostátní):
  `schema-ext.yaml` (vrstva 3 podle ADR 0015), `pitfalls.md` a
  `portals.yaml`. Zapíná se `extensions: [at]` v `repo.yaml`, i spolu
  s `cz`.
- `schema-ext.yaml` přidává jen to, co pilot potřeboval: domovskou
  příslušnost u účastníka (ADR 0051) a událost `church-exit` (pozdější
  poznámka o vystoupení z církve). Nic do zásoby.
- **Pole sdílená dvěma rozšířeními** musí mít stejnou definici; jiná
  definice je chyba rozšíření (`SchemaSet`), aby `[cz, at]` nikdy nezáviselo
  na pořadí.
- **Katalog portálů** `regions/<region>/portals.yaml` místo plánovaného
  `sources.yaml`: pro každý portál `id`, název, adresa, `hosts`, `access`
  (`automated` – adaptér s ověřenými podmínkami; `link` – nástroj jen
  sestaví odkaz; `manual` – nic automaticky, hledá člověk), `adapter`,
  `why` a `notes` ze zkušenosti (bez dat skutečné rodiny). Portál ve dvou
  regionech (Matricula) se musí shodovat ve všem kromě poznámek; poznámky
  se spojí s označením regionu.
- `archive_fetch.py portals [--region at]` katalog vypíše; u portálu
  `manual` nástroj všechny příkazy odmítne (exit 3), nic z portálu nečte
  a vypíše adresu a poznámky. Nové portály (Friedhöfe Wien, WStLA, ANNO,
  Lehmann, digitální archiv SOA Třeboň) jsou `manual`: jejich podmínky
  automatického přístupu nejsou ověřené. Zpřístupnění = adaptér + ověření
  podmínek + nový ADR.
- Katalog se kopíruje do `.proavus/regions/` (spolu se `schema-ext.yaml`),
  takže funguje i z připnuté kopie. `archive_fetch.py` proto potřebuje
  PyYAML (připnutý jako v `pyproject.toml`, ADR 0021).
- `/proavus:start` čte `pitfalls.md` každého regionu z `repo.yaml` a před
  prací s portálem `archive_fetch.py portals`; `/proavus:init` nabízí `cz`
  i `at`.

## Důsledky

- Testy: katalog (regiony, přístupy, shoda adaptérů s kódem včetně `hosts`
  a `why`, sloučení poznámek, chybné záznamy), odmítnutí portálu `manual`
  bez síťového přístupu, `portals` z kopie `.proavus/`, validace s `[at]`
  i `[cz, at]` a kolize definic dvou rozšíření.
- Adresy a hostitelé portálů jsou ze zkušenosti pilotu; když se změní,
  mění se katalog (poznámky), ne kód.
- Existující repo přidá region ručně (`regions` a `extensions`
  v `repo.yaml`, rozhoduje rodina); upgrade to nedělá.
