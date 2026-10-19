# 0022 Dvě osy: hodnocení důkazů a jistota závěru

- **Stav:** přijato (2026-10-20)
- **Původně:** —

## Kontext

Dřívější kódy míchaly vlastnost zdroje a jistotu závěru; QUAY nebyl s ničím propojen.

## Rozhodnutí

Zdroj má **formu** (original / derivative / authored). Každá citace v tvrzení má **informaci** (primary / secondary / undetermined) a **důkaz** (direct / indirect / negative) podle *Evidence Explained*. Závěr (tvrzení, vztah) má **jistotu** (proved / probable / possible / not-proved / disproved). GEDCOM QUAY 0–3 se z nich odvozuje strojově (`proavuslib/quay.py`), nikdy se nezadává.

## Důsledky

Případné starší kódy rodin se převedou tabulkou při převodu dat (rozhodnutí rodiny, ne frameworku).
