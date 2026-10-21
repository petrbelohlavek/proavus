<!-- source: README.md @ v0.5.0 -->
<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="brand/proavus-logo-dark.svg">
    <img src="brand/proavus-logo.svg" alt="Proavus" width="360">
  </picture>
</p>

<p align="center"><a href="README.md">English</a> · <b>Čeština</b><br>
<b>Pro každého</b> · <a href="TECHNICAL.md">Pro techniky (anglicky)</a></p>

**Proavus vám pomůže s Claudem dohledat předky ve starých matrikách –
poctivě, ke každému údaji se zdrojem, a data vaší rodiny zůstanou jen vaší
rodině.**

> **Zatím není dostupný pro každého.** Proavus teď zkoušejí první rodiny.
> Tato stránka popisuje, jak bude fungovat; dnešní stav je v
> [technickém návodu](TECHNICAL.md) (anglicky).

## Co pro vás udělá

- Řeknete Claudovi vlastními slovy, koho hledáte – pradědečka, obec, odkud
  rodina pochází, jméno ze starého dopisu.
- Claude vám pomůže najít správné matriční knihy na portálech archivů
  a staré písmo čte **spolu s vámi**.
- Do rodokmenu se dostane jen to, co zápis dokládá, a u každého údaje
  zůstane zdroj: která kniha, která strana, který zápis. Odhady zůstanou
  označené jako odhady.
- Mezi sezeními se nic neztratí: co se hledalo, co se našlo a co udělat
  příště, je zapsané.

## Jak to celé funguje

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/proavus-architecture-dark.svg">
    <img src="docs/images/proavus-architecture.svg" width="760"
         alt="Vlevo veřejný Proavus pro celý svět, vpravo zamčené domy rodin s jejich rodokmeny. Každá rodina dostane svou kopii Proavus, rodokmen se zpět do veřejné části nedostane.">
  </picture>
</p>

**Jeden Proavus pro všechny, každá rodina zvlášť.** Proavus – postup
a nástroje pro bádání – je veřejný a společně se zlepšuje. Každá rodina si
z něj vezme vlastní kopii do soukromého úložiště (třeba `proavus-novak`),
kam vidí jen ona. Váš rodokmen ani údaje o příbuzných se do veřejné části
nikdy nedostanou.

## Co budete potřebovat

- počítač s Windows nebo macOS;
- účet na [GitHubu](https://github.com) zdarma – tam bude bádání vaší
  rodiny uložené, soukromě;
- [aplikaci Claude](https://claude.ai/download) pro počítač s placeným
  plánem (Pro nebo vyšší).

Programovat umět nemusíte. Všechno ostatní nainstaluje Claude a před každým
krokem se vás zeptá.

## Jak začít

1. Založte si účet na GitHubu a nainstalujte aplikaci Claude.
2. Otevřete aplikaci Claude, přejděte na kartu **Code**, začněte nové
   sezení a napište: *„Nastav mi Proavus.“* Dál vás Claude provede sám:
   nainstaluje, co je potřeba, přihlásí vás v prohlížeči ke GitHubu
   a založí soukromé úložiště vaší rodiny.
3. Každé sezení bádání začněte příkazem **`/proavus:start`** – Claude
   ukáže, kde jste minule skončili a co udělat dál.
4. Řekněte Claudovi, koho hledáte, a čtěte zápisy spolu.
5. Každé sezení ukončete příkazem **`/proavus:end`** – výsledky se
   zkontrolují a uloží i se zdroji.

**Heslo ani kód z GitHubu nikdy nepište do chatu.** Heslo patří jen do
stránky GitHubu v prohlížeči.

## Připojení člena rodiny

Ve více lidech se bádá lépe. Kdo se o úložiště rodiny stará, pozve ostatní
na GitHubu. Nový člen si nainstaluje aplikaci Claude a napíše
**`/proavus:setup`** – Claude nainstaluje, co je potřeba, přihlásí ho
a přidá ho k bádání rodiny. Všichni si na GitHubu zapněte dvoufázové
přihlášení: úložiště obsahuje údaje o žijících příbuzných.

## Vaše data zůstanou vaše

- Bádání vaší rodiny je ve **vašem vlastním soukromém úložišti**; vidí ho
  jen ti, které pozvete.
- U žijících příbuzných se ukládá jen jméno, narození a rodinné vazby –
  u dětí ani datum narození.
- Proavus nikdy nic nezveřejňuje. Mapa rodiny pro lidi mimo rodinu žijící
  osoby sama skryje.

## Co z toho budete mít

Mapu rodiny, kterou otevřete v libovolném prohlížeči: každou osobu, jak
dobře je který údaj doložený a odkud pochází. Ukázka je z mapy smyšlené
testovací rodiny.

<p align="center"><img src="docs/images/map-tree.cs.png" alt="Mapa rodiny: strom předků ve sloupcích generací, karty obarvené podle doložení a čáry podle jistoty" width="800"></p>

## Chcete vědět víc?

- [Technický návod](TECHNICAL.md) (anglicky) – ruční instalace, všechny
  příkazy, nástroje a formát dat
- [Deset pravidel Proavus](method/rules.cs.md) – jak se bádá
- [Licence](TECHNICAL.md#licence) – postup i nástroje jsou volně k použití

© 2026 Petr Bělohlávek a přispěvatelé Proavus.
