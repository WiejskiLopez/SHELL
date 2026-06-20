# Checklists

Checklisty do przejścia przed wysłaniem zmian. Każda odpowiada konkretnej klasie błędu, która już wystąpiła w tym kodzie.

## Dodawanie nowej funkcjonalności (krok po kroku)

1. **Model domenowy** (jeśli potrzeba):
   - Value Object w `domain/value_objects/`
   - Entity/Aggregate Root w `domain/entities/` lub `domain/aggregates/`
   - Domain Event w `domain/events/events/`
   - Domain Exception w `domain/exceptions/`
   - Domain Service w `domain/services/`
   - Repository Port w `domain/repositories/`

2. **Operacja aplikacyjna**:
   - Command lub Query w `application/commands/` lub `application/queries/`
   - Handler w `application/command_handlers/` lub `application/query_handlers/`
   - Event Handler w `application/event_handlers/`
   - DTO w `application/dto/`
   - Mapper w `application/mappers/`

3. **Adapter infrastrukturalny**:
   - ORM Model w `infrastructure/persistence/sql/models/`
   - Migracja Alembic w `infrastructure/persistence/migrations/sql/versions/`
   - Repository w `infrastructure/persistence/sql/repositories/`
   - InMemory Repository w `infrastructure/persistence/memory/`

4. **Rejestracja w DI**:
   - Container w `bootstrap/container/`
   - Factory w `bootstrap/factory/`

5. **Endpoint frameworkowy**:
   - Router FastAPI w `framework/api/routers/`
   - Lub komenda CLI w `framework/cli/commands/`

6. **Testy**:
   - Unit domain w `tests/unit/domain/`
   - Unit application w `tests/unit/application/`
   - Integration w `tests/integration/sql_sqlite/`
   - E2E w `tests/e2e/api/` lub `tests/e2e/cli/`

## Handler completeness

Każdy handler (command/event) musi przejść tę listę:

1. `from __future__ import annotations` na górze pliku
2. `TYPE_CHECKING` — importy domenowe pod guardem jeśli nie są używane w runtime
3. `async with self._uow as uow:` — UoW jako async context manager
4. Pobranie agregatu przez `uow.<repo>.get_by_id()`
5. Mutacja agregatu przez metody domenowe (które wołają `append_event()`)
6. `uow.stage_events(aggregate.pull_events())` — po każdej mutacji
7. Commit przez `__aexit__` — nigdy ręcznego `uow.commit()`
8. Typowanie: sygnatura `handle` z `-> None` dla command, `-> list[Dto]` dla query
9. Brak mutowalnego stanu handlera między wywołaniami (`self._cache = {}` itp.)

## Bootstrap wiring

Przy dodawaniu nowego handlera:

1. **Container**: dodaj `providers.Factory(NewHandler, ...)` w odpowiednim kontenerze
   - Command → `command_container.py`
   - Query → `query_container.py`
   - Event → `event_container.py`
2. **Factory**: zarejestruj handler w odpowiedniej funkcji factory
   - `command_factory.py` → `cmd_bus.register(NewCommand, app_ctx.commands.new_handler_factory)`
   - `query_factory.py` → `q_bus.register(NewQuery, app_ctx.queries.new_handler_factory)`
   - `event_factory.py` → `event_bus.subscribe(NewEvent, app_ctx.events.new_handler_factory)`
3. **Weryfikacja**:
   - Typ komendy/eventu jest unikalny (CommandBus: 1:1, EventBus: 1:N)
   - Kontener ma wszystkie zależności (infra, domain, buses) podpięte
   - `core_container.py` przekazuje wszystkie wymagane zależności do sub-kontenerów

## Mapper symmetry (KRYTYCZNE — zapobiega antywzorcom 1, 7)

Przy każdej zmianie agregatu persystowanego sprawdź round-trip:

1. Każde pole agregatu, które ma przetrwać reload, ma kolumnę w modelu ORM
2. Każda kolumna jest odczytywana w `*_model_to_entity`
3. Każda kolumna jest zapisywana w `*_entity_to_model`
4. Konwersje typów (UUID↔str, datetime↔str, JSON↔dict) są symetryczne w obu kierunkach
5. Zmiana schematu eventu = inkrementacja `schema_version` + obsługa starego formatu w `from_payload()`
6. Test round-trip: `entity → model → entity` — porównaj wszystkie pola

## Lockstep refaktoryzacji (KRYTYCZNE — zapobiega antywzorcowi 1)

Przy odwracaniu/zmianie relacji między agregatami:

1. Agregat domeny: slot, property, `__init__`, metoda domenowa
2. SQL model ORM: kolumna + index/constraint
3. Migracja Alembic: dodanie/usunięcie kolumny + index/constraint
4. Mapper SQL w obu kierunkach: `*_model_to_entity` i `*_entity_to_model`
5. InMemory repo: jeśli zmienia semantykę lookupów
6. Mapper DTO aplikacyjny: `*_to_dpoint`
7. Handlery produkcyjne: ustawiają nowe pole przy tworzeniu agregatu
8. Usunięcie starego pola: grep po wszystkich konsumentach, podmiana źródła danych (antywzorzec 5)

Wszystkie 8 punktów w jednym commicie/PR. Częściowa aktualizacja = gwarantowany runtime błąd.

## Adapter symmetry (KRYTYCZNE — zapobiega antywzorcowi 6)

1. InMemory repo dziedziczy jawnie po tym samym porcie co SQL
2. Każda metoda portu ma pełną implementację w InMemory (nie `return None`)
3. Filtrowanie (`is_current`, `workflow_id` itp.) identyczne jak w SQL
4. Semantyka zapytań listowych (kolejność, unikalność) zgodna między InMemory a SQL
5. Test: ten sam przypadek testowy uruchomiony na InMemory i SQLite daje identyczny wynik

## Persistence round-trip test (KRYTYCZNE — zapobiega antywzorcowi 7)

Dla każdego agregatu persystowanego:

1. Utwórz agregat z nietrywialnym stanem (wypełnione kolekcje, liczniki, waiting sets)
2. Zapisz przez repo SQL
3. Załaduj ponownie przez `get_by_id`
4. Porównaj wszystkie pola — w tym kolekcje wewnętrzne (counters, groups, nodes)
5. Powtórz na InMemory repo — wynik musi być identyczny

## Nazewnictwo i konwencje

| Element | Konwencja | Przykład |
|---------|-----------|----------|
| Pliki z jedną klasą | snake_case | `task_execution_id.py` |
| Katalogi | snake_case | `value_objects/`, `command_handlers/` |
| Klasy | PascalCase | `TaskExecutionId`, `WorkflowStarted` |
| Metody/funkcje | snake_case | `pull_events()`, `get_by_id()` |
| Command/Query | PascalCase + suffix | `StartWorkflowCommand`, `GetWorkflowQuery` |
| Handler | PascalCase + "Handler" | `StartWorkflowHandler` |
| DTO | PascalCase + "Dto" | `WorkflowDto` |
| Domain Event class | PascalCase + `Event` | `TaskExecutionCreatedEvent` |
| Domain Event file | snake_case + `_event` | `task_execution_created_event.py` |
| Exception | PascalCase + domain context | `WorkflowNotFoundException` |
| Port/Protocol | PascalCase | `UnitOfWork`, `IdGenerator` |
| Strategy | PascalCase + "Strategy" | `AgentStrategy` |
| Zmienna ID | suffix `_id` | `workflow_id`, `task_execution_id` |

## Cross-cutting

- Brak komentarzy w kodzie produkcyjnym — kod samodokumentujący się przez nazwy
- Brak emoji w kodzie
- Type hints obowiązkowe (weryfikowane przez mypy, strict mode)
- `__all__` w `__init__.py` — jawny eksport publicznego API
- Importy w kolejności: `from __future__` → stdlib → (pusta linia) → zewnętrzne → (pusta linia) → wewnętrzne
- Linter: ruff; Type checker: mypy (konfiguracja w `shell/pyproject.toml`)

## Testy — strategia

| Kategoria | Lokalizacja | Co testuje | Adaptery |
|-----------|-------------|------------|----------|
| Unit (domain) | `tests/unit/domain/` | Entity, VO, Domain Service, state machine, events | Czyste obiekty domenowe |
| Unit (application) | `tests/unit/application/` | Handlery, bus, strategie | `InMemory*` repositories, `Fake*` porty |
| Integration | `tests/integration/sql_sqlite/` | SQL Reposytoria, UoW, outbox | SQLite (prawdziwa baza) |
| Integration | `tests/integration/sql_postgres/` | PostgreSQL-specific | PostgreSQL przez `PG_TEST_URL` |
| E2E | `tests/e2e/api/` | FastAPI endpointy | httpx + prawdziwy DI container |
| E2E | `tests/e2e/cli/` | CLI komendy | argparse + prawdziwy DI container |
| Architecture | `tests/architecture/test_imports.py` | Zależności importowe | AST parser (nie importuje kodu) |

Reguły:
- Testy jednostkowe nigdy nie używają bazy, frameworka, sieci
- Testy integracyjne i E2E używają `pytest-asyncio` (`asyncio_mode = auto`)
- `InMemory*` adaptery służą do testów — nigdy na produkcji
- W testach integracyjnych: czysta baza na każdą funkcję testową (fixturą)
