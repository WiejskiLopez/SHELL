---
name: directory-naming-standards
description: Reguły nazewnictwa katalogów — snake_case, liczba mnoga, struktura katalogów dla wszystkich warstw.
---

# Directory Naming Standards

> Reguły nazewnictwa katalogów we wszystkich warstwach projektu.

## Podstawowa zasada

Wszystkie katalogi używają `snake_case`. Nazwa katalogu w liczbie mnogiej, oddająca zawartość.

```
value_objects/
command_handlers/
event_handlers/
query_handlers/
query_services/
repositories/
```

## Wzorce nazw katalogów

| Warstwa | Katalog | Zawartość |
|---------|---------|-----------|
| Domain | `aggregates/<nazwa_agregatu>/` | Aggregate Root |
| Domain | `aggregates/<nazwa_agregatu>/entities/` | Child entities |
| Domain | `aggregates/<nazwa_agregatu>/events/` | Domain Events |
| Domain | `aggregates/<nazwa_agregatu>/value_objects/` | Value Objects (w tym ID) |
| Domain | `domain/platform/base/` | Entity/AggregateRoot base classes |
| Domain | `domain/platform/value_objects/` | Universalne VO platformy |
| Domain | `domain/platform/ports/` | Porty platformy (Clock, IdGenerator) |
| Domain | `domain/platform/events/` | DomainEvent base class |
| Domain | `domain/platform/exceptions.py` | DomainError base |
| Domain | `domain/<bc>/aggregates/<agregat>/repositories/` | Porty repozytoriów per agregat |
| Domain | `domain/<bc>/aggregates/<agregat>/services/` | Domain Services per agregat |
| Domain | `domain/<bc>/aggregates/<agregat>/exceptions/` | Domain Exceptions per agregat |
| Application | `application/<bc>/commands/<aggregate>/` | Komendy per agregat |
| Application | `application/<bc>/command_handlers/<aggregate>/` | Handlery komend per agregat |
| Application | `application/<bc>/queries/<aggregate>/` | Query per agregat |
| Application | `application/<bc>/query_handlers/<aggregate>/` | Handlery query per agregat |
| Application | `application/<bc>/query_services/` | QueryServices |
| Application | `application/<bc>/events/<aggregate>/` | Eventy per agregat |
| Application | `application/<bc>/event_handlers/<aggregate>/` | Handlery eventów per agregat |
| Application | `application/<bc>/messages/<aggregate>/` | Message per agregat |
| Application | `application/<bc>/message_handlers/<aggregate>/` | Handlery message per agregat |
| Application | `application/<bc>/sagas/<aggregate>/` | Sagi per agregat |
| Application | `application/<bc>/dto/<aggregate>/` | DTO odpowiedzi per agregat |
| Application | `application/<bc>/mappers/<aggregate>/` | Mappery per agregat |
| Application | `application/<bc>/ports/` | Porty aplikacyjne |
| Application | `application/strategies/<nazwa>/` | Strategie |
| Domain | `domain/<bc>/aggregates/<aggregate>/services/` | Domain Services per agregat |
| Domain | `domain/<bc>/descriptors/` | SemanticDescriptory |
| Infrastructure | `infrastructure/<bc>/<aggregate>/persistence/sql/repositories/` | SQL repozytoria per agregat |
| Infrastructure | `infrastructure/<bc>/<aggregate>/persistence/memory/` | InMemory repozytoria per agregat |
| Infrastructure | `infrastructure/<bc>/<aggregate>/persistence/sql/models/` | ORM modele per agregat |
| Infrastructure | `infrastructure/<bc>/<aggregate>/persistence/sql/mappers/` | Mappery ORM per agregat |
| Infrastructure | `infrastructure/<bc>/acl/` | Anti-Corruption Layer |
| Infrastructure | `infrastructure/platform/time/` | Adaptery uniwersalne (zegar) |
| Infrastructure | `infrastructure/platform/identity/` | Adaptery uniwersalne (IdGenerator) |
| Infrastructure | `infrastructure/platform/persistence/migrations/sql/versions/` | Migracje Alembic |
| Framework | `framework/<bc>/<aggregate>/api/` | Routery FastAPI per agregat |
| Framework | `framework/<bc>/entrypoints/` | Entrypointy (agent, planner, worker) |
| Process | `process/<bc>/<nazwa_sagi>/` | Saga state machine (<nazwa>_saga.py, state.py) |
| Process | `process/<bc>/<nazwa_sagi>/handlers/` | Event handlery delegujące do sagi |
| Process | `process/<bc>/<nazwa_sagi>/commands/` | Komendy produkowane tylko przez tę sagę |
| Process | `process/<bc>/<nazwa_sagi>/ports/` | Porty (Protocol) dla repozytorium i command publishera |
| Bootstrap | `bootstrap/<bc>/container/` | DI per BC |
| Bootstrap | `bootstrap/platform/container/` | Containery platformowe |
| Bootstrap | `bootstrap/platform/factory/` | Factory (command_factory, event_factory) |
| Test | `tests/<bc>/unit/domain/` | Testy jednostkowe domeny per BC |
| Test | `tests/<bc>/unit/application/` | Testy jednostkowe aplikacji per BC |
| Test | `tests/<bc>/integration/sql_sqlite/` | Testy integracyjne SQLite per BC |
| Test | `tests/<bc>/integration/sql_postgres/` | Testy integracyjne Postgres per BC |
| Test | `tests/<bc>/e2e/api/` | Testy E2E API per BC |
| Test | `tests/<bc>/e2e/cli/` | Testy E2E CLI per BC |
| Test | `tests/process/unit/` | Testy jednostkowe process (saga state machine) |
| Test | `tests/process/integration/sql_sqlite/` | Testy integracyjne process z SQLite |
| Test | `tests/platform/architecture/` | Testy architektury |

> **Szczegółowe reguły → [naming-convention-standard](../naming-convention-standard/SKILL.md)**

## Ograniczenia

- Nazwy katalogów zawsze w liczbie mnogiej (wyjątek: nazwy agregatów)
- `snake_case` — małe litery, podkreślenia
- Jeden poziom zagłębienia dla encji/eventów/VO wewnątrz agregatu
- Żadnych skrótów w nazwach katalogów
