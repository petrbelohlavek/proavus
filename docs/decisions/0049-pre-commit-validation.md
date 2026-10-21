# 0049 Validace před každým commitem v rodinném repu (hook `pre-commit`)

- **Stav:** přijato (2026-10-21)
- **Původně:** —
- **Upřesňuje:** [ADR 0016](0016-pilot-without-reviewers-identity-gate.md), [ADR 0009](0009-init-and-upgrade.md)

## Kontext

V pilotu se ukládá rovnou do `main` bez schvalovatelů (ADR 0016); data chrání
jen validace. Tu zatím spouštěly skilly (`/proavus:end`, `/proavus:upgrade`)
a workflow na GitHubu – ten ale chybu najde až po pushnutí, kdy už je
v historii a u ostatních členů. Commit mimo skill (claim otázky, ruční
oprava, jiný agent) nekontroloval nikdo. Členové rodiny mají Windows
i macOS, často bez systémového Pythonu.

## Rozhodnutí

- Šablona rodinného repa má **`.githooks/pre-commit`** v Pythonu (ne
  v Bashi). Spouští se přes `uv` (`#!/usr/bin/env -S uv run --script`), který
  Proavus vyžaduje tak jako tak; hook sám nemá závislosti.
- Hook validuje **přesně to, co se ukládá**: obsah indexu zkopíruje do
  dočasné složky (`git checkout-index`) a pustí na něj
  `.proavus/tools/validate.py` z téže kopie. Neuložené rozpracované soubory
  commit nezastaví a chyba v ukládané verzi neprojde.
- Při chybě vypíše chyby validátoru a zprávu česky i anglicky („Commit
  zastaven … / Commit stopped …“) a commit zastaví. Chybí-li `uv` nebo
  `.proavus/tools/validate.py`, commit také zastaví a řekne, co spustit
  (`/proavus:setup`, `/proavus:upgrade`). Varování commit nezastaví.
- **`family_repo.py hooks`** nastaví `core.hooksPath = .githooks`
  a spustitelnost hooku – na disku i v gitu (`update-index --chmod=+x`),
  protože repo založené na Windows by jinak předalo hook bez příznaku a git
  na macOS by ho ignoroval. `core.hooksPath` se neklonuje, proto ho zapínají
  `/proavus:init`, `/proavus:setup` (po naklonování), `/proavus:start` (po
  `git pull`, kdy mohl přijít hook z upgradu jiného člena) a
  `/proavus:upgrade`; nástroj je idempotentní.
- Hook je soubor frameworku jako workflow: přidá a obnoví ho jen
  `/proavus:upgrade`.
- Skilly dál validují **před** commitem samy (i claim otázky a po `git pull`
  v `/proavus:end`), aby chyby vysvětlily dřív, než je zastaví hook. Hook se
  nikdy neobchází (`--no-verify`, změna `core.hooksPath`) – pravidlo je
  v bloku Proavus v `AGENTS.md`.

## Důsledky

- Test na fiktivním repu: repo ze šablony, `git init`, `hooks`, commit bez
  chyb projde, commit s chybnou osobou se zastaví s oběma zprávami, chybný
  soubor mimo commit nevadí; upgrade přidá hook a zapne ho. Test hooku běží
  jen tam, kde je `uv` a POSIX (CI na Ubuntu); spuštění přes Git for Windows
  (`env -S` z jeho coreutils) zatím ověřeno v testu není.
- Commit trvá o validaci déle (sekundy; první spuštění `uv` stáhne
  závislosti validátoru).
- Kdo commituje mimo Proavus nebo hook vypne, kontrolu obejde; pojistkou
  zůstává workflow na GitHubu.
- Repa do 0.4.0 hook nemají, dokud neproběhne `/proavus:upgrade`;
  `/proavus:start` i `/proavus:setup` to řeknou.
