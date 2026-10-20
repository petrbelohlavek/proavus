# 0027 Mapa rodiny jako jeden soběstačný soubor HTML

- **Stav:** přijato (2026-10-20); rozvržení stránky nahrazeno [ADR 0028](0028-family-map-layout.md)
- **Původně:** —

## Kontext

Rodina potřebuje strom vidět, ne jen číst soubory. Architektura počítá s
generovanou mapou (`tools/build_views.py`, kap. 5), která se neukládá do gitu
([ADR 0019](0019-generated-outputs-not-in-git.md)). Mapa ukazuje data
soukromého repa, takže nesmí nic posílat ven, a musí ukázat nejistotu, ne
jen „čistý“ strom.

## Rozhodnutí

- `uv run .proavus/tools/build_views.py .` zapíše `views/mapa.html`: **jeden
  soubor bez CDN a bez externích zdrojů** (styl, skript i kresba stromu v SVG
  jsou uvnitř; Content-Security-Policy zakazuje načítat cokoli zvenku). Otevře
  se offline v prohlížeči; odkazy na archivy se otevřou jen kliknutím.
- **Výchozí osoba** je `map.root` v `repo.yaml` (lze přepsat `--root`);
  `map.lang` volí popisky (`en`, `cs`). Validátor hlídá, že `map.root` je
  osoba.
- **Strom předků** vede přes vztahy `parent-child` z `relationships/`. Čára
  ukazuje jistotu vztahu: prokázáno plná, pravděpodobné čárkovaná, možné
  tečkovaná, neprokázáno řídce tečkovaná; vyvrácený vztah se nekreslí.
  Nevlastní rodiče (step, adoptive, foster, guardian) jsou ve stromu odlišení,
  ale jejich předci se dál nerozvíjejí – strom je linie předků. Výslovně
  neznámý rodič (`unknown`) má vlastní prázdné pole. Osoba, která už ve stromu
  je (zhroucení předků, cyklus), se podruhé jen označí.
- **Karta osoby:** jména, údaje z tvrzení s datem, místem, jistotou a citací
  (záznam s lokátorem, zdroj, odkaz do archivu, QUAY odvozené podle ADR
  0022), výskyty v záznamech (tvrzení identity), rodiče, partneři, děti,
  otevřené rozpory a otevřené otázky. Karty mají i osoby mimo strom.
- **Žijící osoby** (pravidlo 9, [ADR 0025](0025-living-persons.md)) se
  rozpoznají stejně jako ve validátoru a mapa i u chybných dat ukáže jen
  jméno, pohlaví, narození a vztahy; u nezletilých bez data narození, u vztahů
  žijících bez dat; rozpory a otázky o žijících jen jako ID.

## Důsledky

Mapa je jen pohled: opravuje se zdroj a mapa se vygeneruje znovu. Soubor
obsahuje data rodiny, proto zůstává ve `views/` mimo git a nesdílí se
veřejně. Velké stromy se posouvají vodorovně; hledání a GEDCOM přijdou, až je
vyžádá výzkum (ADR 0013).
