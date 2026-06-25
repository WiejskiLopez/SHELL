---
name: factory
description: Wzorzec Factory w DDD — odpowiedzialność tworzenia złożonych agregatów, rekonstrukcja z persistance, factory methods na VO/Entity, AggregateFactory. Używaj gdy tworzenie agregatu wymaga skomplikowanej logiki, rekonstruujesz obiekt z bazy, albo potrzebujesz scentralizować logikę tworzenia.
---

# Factory Pattern w Enterprise DDD

## 1. Factory a Mapper — Różnice

| Aspekt | Factory | Mapper |
|--------|---------|--------|
| Odpowiedzialność | Tworzy nowe obiekty | Konwertuje między warstwami |
| Walidacja | Tak (biznesowa) | Nie (zakłada że dane są poprawne) |
| Używane w | Handlerach, Domain Services | Repozytoriach |
| Źródło danych | Komendy, eventy, dane wejściowe | Modele ORM, DTO |
| Output | Agregaty, encje, VO | Agregaty, encje, DTO |

## 2. Podsumowanie — Checklista

Projektując Factory:
- [ ] Factory w domenie — brak importów infrastrukturalnych
- [ ] Lokalizacja: `shell/domain/<bc>/factories/`
- [ ] Testy jednostkowe dla każdej ścieżki tworzenia
