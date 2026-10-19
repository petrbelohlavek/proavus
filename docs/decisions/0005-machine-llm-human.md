# 0005 Princip práce: stroj → LLM → člověk

- **Stav:** přijato (2026-10-20)
- **Původně:** R9

## Kontext

LLM se mýlí v čtení i úsudku; člověk nemá kapacitu kontrolovat všechno.

## Rozhodnutí

Co jde, řeší skript (ID, kontroly, přepočty, dotazy). LLM navrhuje, čte, vysvětluje. Člověk rozhoduje o identitě, o změnách stromu a o tom, co je „prokázáno“. Každé pravidlo metodiky, které jde zkontrolovat strojem, se převede do validátoru.

## Důsledky

`validate.py` je hlavní pojistka kvality. Text metodiky vysvětluje důvody; lidské rozhodování je omezeno na místa, kde je nezastupitelné.
