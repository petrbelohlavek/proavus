# 0004 Zdroj pravdy je Markdown + YAML v gitu

- **Stav:** přijato (2026-10-20)
- **Původně:** R8

## Kontext

Data musí vydržet desítky let, být čitelná pro člověka i LLM, slučovat se přes git a mít historii změn. GEDCOM jako jeden soubor způsobuje konflikty a má slabý model důkazů; databázový server potřebuje provoz.

## Rozhodnutí

1 entita = 1 soubor Markdown se záhlavím YAML; důkazy jako výřezy JPEG a originály dokumentů. SQLite jen jako odvozený lokální index; GEDCOM, HTML a přehledy se generují. Žádný databázový server.

## Důsledky

Kázeň formátu hlídá schéma a `validate.py` od první verze. Dotazy přes celý strom řeší odvozený index. webtrees může sloužit jen jako publikační vrstva (jednosměrný import GEDCOM).
