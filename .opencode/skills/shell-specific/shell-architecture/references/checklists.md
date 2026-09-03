# Checklists

Checklisty do przejścia przed wysłaniem zmian. Każda odpowiada konkretnej klasie błędu, która już wystąpiła w tym kodzie.

## Dodawanie nowej funkcjonalności (krok po kroku)

> Konwencja ścieżek: SHELL nie ma top-level pakietów `domain/`, `application/`, `infrastructure/`, `framework/`, `bootstrap/`. Każdą ścieżkę poniżej czytaj jako `shell/<bc>_service/<warstwa>/<bc>/...` (np. `domain/<bc>/aggregates/<agregat>/` = `shell/execution_service/domain/execution/aggregates/<agregat>/`).

1. **Model domenowy** (jeśli potrzeba):
   - Value Object w `domain/<bc>/aggregates/<agregat>/value_objects/`
   - Entity/Aggregate Root w `domain/<bc>/aggregates/<agregat>/`
   - Domain Event w `domain/<bc>/aggregates/<agregat>/events/`
   - Domain Exception w `domain/<bc>/aggregates/<agregat>/exceptions/`
   - Domain Service w `domain/<bc>/aggregates/<agregat>/services/` (lub `domain/<bc>/services/`)
   - Repository Port w `domain/<bc>/aggregates/<agregat>/repositories/`

2. **Operacja aplikacyjna** (atomowa, 1 agregat):
   - Command lub Query w `application/<bc>/<aggregate>/commands/` lub `application/<bc>/<aggregate>/queries/`
   - Handler w `application/<bc>/<aggregate>/command_handlers/` lub `application/<bc>/<aggregate>/query_handlers/`
   - Event Handler w `application/<bc>/<aggregate>/event_handlers/`
   - DTO w `application/<bc>/<aggregate>/dto/`
   - Mapper w `application/<bc>/<aggregate>/mappers/`

3. **Orkiestracja/Process** (jeśli potrzeba koordynacji wielu agregatów — warstwa docelowa):
   - Saga/Process Manager w `process/<bc>/<nazwa_sagi>/manager.py`
   - Saga State w `process/<bc>/<nazwa_sagi>/state.py`
   - Event Handlery sagi w `process/<bc>/<nazwa_sagi>/handlers/`
   - Saga-specific commands w `process/<bc>/<nazwa_sagi>/commands/`
   - Saga ports (Protocol) w `process/<bc>/<nazwa_sagi>/ports/`

4. **Adapter infrastrukturalny**:
   - ORM Model w `infrastructure/<bc>/<aggregate>/persistence/sql/models/`
   - Migracja Alembic w `<bc>_service/migrations/versions/` (per BC)
   - Repository w `infrastructure/<bc>/<aggregate>/persistence/sql/repositories/`
   - InMemory Repository w `infrastructure/<bc>/<aggregate>/persistence/memory/`

5. **Rejestracja w DI**:
   - Container w `bootstrap/<bc>/container/<bc>_core_container.py`

6. **Endpoint frameworkowy**:
   - Router FastAPI w `framework/<bc>/<aggregate>/api/`
   - Lub komenda CLI w `framework/<bc>/api/` / `bootstrap/<bc>/cli/`

7. **Testy**:
   - Unit domain w `tests/<bc>_service/unit/domain/`
   - Unit application w `tests/<bc>_service/unit/application/`
   - Unit process w `tests/process/unit/` (wzorzec docelowy)
   - Integration process w `tests/process/integration/sql_sqlite/` (wzorzec docelowy)
   - Integration w `tests/<bc>_service/integration/sql_sqlite/`
   - E2E w `tests/<bc>_service/e2e/api/` lub `tests/<bc>_service/e2e/cli/`

## Handler completeness

Każdy handler (command/event) musi przejść tę listę:

1. `from __future__ import annotations` na górze pliku
2. `TYPE_CHECKING` — importy domenowe pod guardem jeśli nie są używane w runtime
3. `async with self._unit_of_work as unit_of_work:` — UoW jako async context manager
4. Pobranie agregatu przez `unit_of_work.<repository>.get_by_id()`
5. Mutacja agregatu przez metody domenowe (które wołają `append_event()`)
6. `unit_of_work.stage_events(aggregate.pull_events())` — po każdej mutacji
7. Commit przez `__aexit__` — nigdy ręcznego `unit_of_work.commit()`
8. Typowanie: sygnatura `handle` z `-> None` dla command, `-> list[Dto]` dla query
9. Brak mutowalnego stanu handlera między wywołaniami (`self._cache = {}` itp.)

## Bootstrap wiring

Przy dodawaniu nowego handlera:

1. **Container**: dodaj `providers.Factory(NewHandler, ...)` w kontenerze danego BC (`shell/<service>/bootstrap/<bc>/container/<bc>_core_container.py`) — nazwa `*_handler_factory`
2. **Rejestracja na busie**: w kontenerze/funkcji setup danego BC
   - `command_bus.register(NewCommand, container.new_command_handler_factory)`
   - `query_bus.register(NewQuery, container.new_query_handler_factory)`
   - `event_bus.subscribe(NewEvent, container.new_event_handler_factory)`
3. **Weryfikacja**:
   - Typ komendy/eventu jest unikalny (CommandBus: 1:1, EventBus: 1:N)
   - Kontener ma wszystkie zależności podpięte (odpowiada za nie test kontenera)
   - Spójność rejestracji sprawdza `application-layer/handler-registration-integrity` i testy architektury (`test_container_delivery_bundle_wiring`)

## Mapper symmetry (KRYTYCZNE — zapobiega antywzorcom 1, 7)

Przy każdej zmianie agregatu persystowanego sprawdź round-trip:

1. Każde pole agregatu, które ma przetrwać reload, ma kolumnę w modelu ORM
2. Każda kolumna jest odczytywana w `*_model_to_entity`
3. Każda kolumna jest zapisywana w `*_entity_to_model`
4. Konwersje typów (UUID↔str, datetime↔str, JSON↔dict) są symetryczne w obu kierunkach
5. Zmiana schematu eventu = nowa `schema_version` + obsługa starego formatu przez upcaster (`IntegrationEventDeserializer`)
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

## Cross-cutting

- Brak komentarzy w kodzie produkcyjnym — kod samodokumentujący się przez nazwy
  - **Wyjątek:** komentarze `# noqa: <REGULA> — <uzasadnienie>` są obowiązkowe dla każdej świadomie stłumionej reguły lintera. Każde `# noqa` musi zawierać kod reguły i konkretne uzasadnienie dlaczego w TYM miejscu reguła nie ma zastosowania. Patrz skill `noqa-enterprise-policy`.
- Brak emoji w kodzie
- Type hints obowiązkowe (weryfikowane przez mypy, strict mode)
- `__all__` w `__init__.py` — jawny eksport publicznego API
- Importy w kolejności: `from __future__` → stdlib → (pusta linia) → zewnętrzne → (pusta linia) → wewnętrzne
- Linter: ruff; Type checker: mypy (konfiguracja w `shell/pyproject.toml`)

## Testy — strategia

| Kategoria | Lokalizacja | Co testuje | Adaptery |
|-----------|-------------|------------|----------|
| Unit (domain) | `tests/<bc>/unit/domain/` | Entity, VO, Domain Service, state machine, events | Czyste obiekty domenowe |
| Unit (application) | `tests/<bc>/unit/application/` | Atomowe handlery, bus, strategie | `InMemory*` repositories, `Fake*` porty |
| Unit (process) | `tests/process/unit/` | Saga state machine, Process Manager handlery | `InMemory*` saga repo, `FakeCommandPublisher` |
| Integration (process) | `tests/process/integration/sql_sqlite/` | Saga repository + manager na SQLite | SQLite |
| Integration | `tests/<bc>/integration/sql_sqlite/` | SQL Reposytoria, UoW, outbox | SQLite (prawdziwa baza) |
| Integration | `tests/<bc>/integration/sql_postgres/` | PostgreSQL-specific | PostgreSQL przez `PG_TEST_URL` |
| E2E | `tests/<bc>/e2e/api/` | FastAPI endpointy | httpx + prawdziwy DI container |
| E2E | `tests/<bc>/e2e/cli/` | CLI komendy | argparse + prawdziwy DI container |
| Architecture | `shell/tests/architecture/` | Zależności importowe, konwencje, typy | AST parser (nie importuje kodu) |

Reguły:
- Testy jednostkowe nigdy nie używają bazy, frameworka, sieci
- Testy integracyjne i E2E używają `pytest-asyncio` (`asyncio_mode = auto`)
- `InMemory*` adaptery służą do testów — nigdy na produkcji
- W testach integracyjnych: czysta baza na każdą funkcję testową (fixturą)
