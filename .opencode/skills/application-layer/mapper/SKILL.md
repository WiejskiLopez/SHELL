---
name: mapper
description: Zasady projektowania mapperów w architekturze hexagonalnej — konwersja między warstwami (domain ↔ model ORM, domain ↔ DTO), symetryczność mapowania, round-trip testing. Używaj gdy implementujesz nowy mapper dla agregatu, refaktoryzujesz istniejący, albo potrzebujesz mapowania między warstwami.
---

# Mapper Pattern w Enterprise DDD

## 1. Mapper a Factory — Różnice

| Aspekt | Mapper | Factory |
|--------|--------|---------|
| Cel | Konwersja między warstwami | Tworzenie nowych obiektów |
| Walidacja | Nie (zakłada poprawne dane) | Tak (biznesowa) |
| Używa `restore()` | Tak (do odczytu) | Tak (do rekonstrukcji) |
| Zależności | Tylko typy proste + VO | Domain Services, inne fabryki |
| Lokalizacja | Infrastruktura | Domeny |

## 2. Lokalizacja

```
# Mapper ORM (infrastructure) — per agregat w persistence
shell/<service>/infrastructure/<bc>/<aggregate>/persistence/sql/mappers/<aggregate>_mapper.py

# Mapper DTO (application) — per agregat
shell/<service>/application/<bc>/<aggregate>/mappers/<aggregate>_dto_mapper.py

# Mapper Command (application) — per agregat
shell/<service>/application/<bc>/<aggregate>/mappers/<command>_mapper.py
```

## 3. Podsumowanie — Checklista

Tworząc mapper:
- [ ] Lokalizacja: infrastruktura (ORM) lub aplikacja (DTO)
- [ ] Round-trip test w testach jednostkowych
- [ ] Osobny mapper dla ORM i DTO
- [ ] Brak zależności między mapperami różnych warstw
