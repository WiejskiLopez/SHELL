---
name: repository
description: Zasady projektowania repozytoriów w DDD — porty w domenie, implementacje SQL/InMemory w infrastrukturze, granularność metod, paginacja, transakcyjność. Używaj gdy projektujesz nowe repozytorium dla agregatu, refaktoryzujesz istniejące, albo definiujesz kontrakt między domeną a infrastrukturą.
---

# Repository Pattern w Enterprise DDD

## 1. Lokalizacja

```
shell/domain/<bc>/repositories/          # Porty (ABC/Protocol)
├── execution_repository.py              # Port
├── in_memory_execution_repository.py    # Implementacja testowa
└── graph_repository.py                  # Port
```

```
shell/infrastructure/<bc>/repositories/  # Adaptery (SQL)
├── sql_execution_repository.py
└── sql_graph_repository.py
```

## 2. Podsumowanie — Checklista

Projektując repozytorium:
- [ ] Port (ABC) w `shell/domain/<bc>/repositories/`
- [ ] Adapter SQL w `shell/infrastructure/<bc>/repositories/`
- [ ] Testy jednostkowe na InMemory
- [ ] Testy integracyjne na SQL implementacji
