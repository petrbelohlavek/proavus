# 0006 Dlouhodobě vlastní úložiště a sdílení mezi rodinami

- **Stav:** navrženo (2026-10-20)
- **Původně:** R10

## Kontext

GitHub nenabízí účty bez GitHubu, vynucenou kontrolu změn v soukromých repech zdarma ani sdílení mezi rodinami.

## Rozhodnutí

Postupně GitHub → vlastní git server (Forgejo/Gitea) → genealogická služba (API + MCP): sdílený registr prohledaného, shoda předků, katalog zdrojů. Výzkum a LLM zůstávají u uživatele; server nevolá LLM ani nečte archivy.

## Důsledky

Datový formát je od začátku stejný pro všechny kroky. Každý krok vyžaduje doloženou potřebu, právní posouzení a model financování.
