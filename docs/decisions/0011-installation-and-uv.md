# 0011 Instalace: aplikace Claude + `/setup`; nástroje přes `uv`

- **Stav:** přijato (2026-10-20)
- **Původně:** R16

## Kontext

Rodina nemá technické znalosti; Python na Windows a novějším macOS chybí.

## Rozhodnutí

Uživatel nainstaluje jen aplikaci Claude a založí účet na GitHubu; zbytek provede průvodce `/setup` se souhlasem uživatele (git, `gh`, `uv`, přihlášení přes prohlížeč, plugin, `/init` nebo stažení rodinného repa) a `/check` diagnostikuje potíže. Nástroje v Pythonu se spouští `uv run` (Python si `uv` stáhne sám). Dva kanály pluginu: správce lokální katalog, rodina větev `stable`.

## Důsledky

Hooky a skripty jen v Pythonu (Windows bez Bashe). Automatické aktualizace pluginu je nutné zapnout ručně v `/plugin`. Odchylka „jen standardní knihovna“ viz ADR 0021.
