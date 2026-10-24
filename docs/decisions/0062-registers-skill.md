# 0062 Skill pro hledání v matrikách (`/proavus:registers`)

- **Stav:** přijato (2026-10-24)
- **Původně:** —
- **Navazuje na:** [ADR 0058](0058-source-volumes.md),
  [ADR 0059](0059-second-reading.md), [ADR 0060](0060-index-pointers.md),
  [ADR 0061](0061-page-image-anchors.md)

## Kontext

Pátrání v matrikách má stálý postup – index → kniha → svazek → strana →
snímek – a stálé pasti: číslo v indexu je strana i folio, svazky nejdou po
sobě, posun strana → snímek se mění, okrajová poznámka je pozdější než
zápis, negativ z indexu není důkaz. Metoda (`reading-records.md`) popisuje,
jak zapsat zápis, ne pořadí práce kolem něj. Agent ho skládal ze `start`
a z metody pokaždé znovu.

## Rozhodnutí

Nový skill `skills/registers/SKILL.md` (`/proavus:registers`), který smí
použít i agent sám, když otázka vede do matriky. Obsah: příprava (otázka,
všechny tvary jména, správná kniha, přístup k portálu), index jako zdroj
ukazatelů, kniha a svazek, strana → snímek přes `locate.py` a kotvy,
kontrola záhlaví, sousedních zápisů a okrajů, zápis se slepým druhým
čtením, coverage knihy s `followed` a zásady pro negativní výsledky.
Skill jen řadí práci a odkazuje na metodu; pravidla a pole se v něm
neopakují jinak, než jak je stanoví metoda a ADR 0058–0061.

## Důsledky

Skill je součást pluginu, do rodinného repozitáře se nekopíruje
a k uživateli přijde s aktualizací pluginu. Evaly pro svazek mimo pořadí
a zlom v číslování snímků jsou další krok.
