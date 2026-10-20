# 0030 Migrace i v menších verzích: sjednocení dat

- **Stav:** přijato (2026-10-20)
- **Původně:** —
- **Doplňuje:** [ADR 0018](0018-single-semantic-version.md)

## Kontext

Schéma 0.3 přidává novou podobu údajů, které už v datech jsou (`crops` místo `crop`, úkoly se stavem místo textu). Stará podoba zůstává platná (přidání podle ADR 0015), ale dvě podoby téhož ztěžují nástroje i čtení. ADR 0018 počítal s `migrate.py` jen u hlavní verze.

## Rozhodnutí

`migrate.py` vede migrace podle verze, která je přinesla (`MIGRATIONS["0.3.0"]`). `/proavus:upgrade` spustí každou, kterou upgrade překročí:

- **hlavní verze** (zásadní změna schématu) migraci mít **musí** – bez ní se upgrade odmítne (beze změny proti ADR 0018);
- **menší verze** ji mít **smí**: přepíše data do nové preferované podoby, stará podoba dál platí. Taková migrace nic neztratí, jde spustit opakovaně a mění jen hlavičky souborů, které převádí. Tělo ani význam dat se nemění; hlavičku zapíše v ručním stylu (krátké seznamy `[a, b]`, odsazené odrážky, data bez uvozovek), ztratí se jen nepovinné uvozovky a komentáře v hlavičce.

První je 0.3.0: `crop` → `crops`, úkoly zadané textem → `{task, status: open}`.

## Důsledky

Rodinné repo po upgradu používá jen nové podoby; nástroje starou podobu dál čtou (repa, která upgrade ještě neprovedla, a ruční zápisy). Migraci menší verze nikdy nesmí potřebovat validace.
