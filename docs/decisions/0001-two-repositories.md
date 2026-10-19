# 0001 Dvě repa: framework a soukromé repo rodiny

- **Stav:** přijato (2026-10-20)
- **Původně:** R1

## Kontext

Framework má být jednou veřejný, data rodiny nikdy. Smíchání v jednom repu by data nechalo v historii frameworku; vyčlenění později je riskantní. Git submodule je pro rodinu i agenty zbytečně složitý.

## Rozhodnutí

Dvě samostatná repa vedle sebe v pracovní složce `Proavus/` (jen složka, ne git, mimo synchronizovaná úložiště): framework `proavus` a data rodiny `proavus-<rodina>`. Rodinné repo framework používá jako plugin a nikdy ho do sebe nekopíruje (kromě připnuté kopie nástrojů, ADR 0014).

## Důsledky

Čisté oddělení a žádné riziko úniku dat přes historii. Každá rodina má vlastní repo. Synchronizovaná úložiště (iCloud, Dropbox, OneDrive) se pro `Proavus/` nepoužívají – poškozují složku `.git`; zálohu zajišťuje vzdálené repo.
