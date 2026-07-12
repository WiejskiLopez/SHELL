---
name: repository
description: Zasady projektowania repozytoriów w DDD — porty w domenie, implementacje SQL/InMemory w infrastrukturze, granularność metod, paginacja, transakcyjność. Używaj gdy projektujesz nowe repozytorium dla agregatu, refaktoryzujesz istniejące, albo definiujesz kontrakt między domeną a infrastrukturą.
---

# Repository Pattern w Enterprise DDD

## 1. Lokalizacja

```
shell/domain/<bc>/aggregates/<agregat>/repositories/   # Porty (Protocol) per agregat
├── execution_repository.py                             # Port
└── graph_execution_repository.py                       # Port
```

```
shell/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/  # Adaptery (SQL) per agregat
├── sql_execution_repository.py
└── sql_graph_execution_repository.py
```

```
shell/infrastructure/<bc>/<aggregate>/persistence/memory/            # InMemory (testy) per agregat
├── in_memory_execution_repository.py
└── in_memory_graph_execution_repository.py
```

## 2. Podsumowanie — Checklista

Projektując repozytorium:
- [ ] Port (Protocol) w `shell/domain/<bc>/aggregates/<agregat>/repositories/`
- [ ] Adapter SQL w `shell/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/`
- [ ] Adapter InMemory w `shell/infrastructure/<bc>/<aggregate>/persistence/memory/`
- [ ] Testy jednostkowe na InMemory
- [ ] Testy integracyjne na SQL implementacji
