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
| Domain | `domain/value_objects/` | Universalne VO platformy |
| Domain | `domain/entities/base/` | Entity/AggregateRoot base classes |
| Domain | `domain/repositories/` | Porty repozytoriów |
| Domain | `domain/services/` | Domain Services |
| Domain | `domain/exceptions/` | Domain Exceptions |
| Domain | `domain/ports/` | Porty (tylko platform) |
| Application | `application/<bc>/commands/` | Komendy |
| Application | `application/<bc>/command_handlers/` | Handlery komend |
| Application | `application/<bc>/queries/` | Query |
| Application | `application/<bc>/query_handlers/` | Handlery query |
| Application | `application/<bc>/query_services/` | QueryServices |
| Application | `application/<bc>/event_handlers/` | Handlery eventów |
| Application | `application/<bc>/dto/` | DTO odpowiedzi |
| Application | `application/<bc>/mappers/` | Mappery |
| Application | `application/<bc>/ports/` | Porty aplikacyjne |
| Application | `application/strategies/<nazwa>/` | Strategie |
| Infrastructure | `infrastructure/<bc>/repositories/` | SQL repozytoria |
| Infrastructure | `infrastructure/<bc>/adapters/` | Adaptery serwisów |
| Infrastructure | `infrastructure/<bc>/acl/` | Anti-Corruption Layer |
| Infrastructure | `infrastructure/platform/adapters/` | Adaptery uniwersalne |
| Infrastructure | `infrastructure/persistence/sql/models/` | ORM modele |
| Infrastructure | `infrastructure/persistence/sql/mappers/` | Mappery ORM |
| Infrastructure | `infrastructure/persistence/sql/repositories/` | SQL repozytoria |
| Infrastructure | `infrastructure/persistence/memory/` | InMemory repozytoria |
| Infrastructure | `infrastructure/persistence/migrations/sql/versions/` | Migracje Alembic |
| Framework | `framework/api/routers/` | Routery FastAPI |
| Framework | `framework/cli/commands/` | Komendy CLI |
| Bootstrap | `bootstrap/<bc>/` | DI per BC |
| Bootstrap | `bootstrap/container/` | Containery |
| Bootstrap | `bootstrap/factory/` | Factory |
| Test | `tests/unit/domain/` | Testy jednostkowe domeny |
| Test | `tests/unit/application/` | Testy jednostkowe aplikacji |
| Test | `tests/integration/sql_sqlite/` | Testy integracyjne SQLite |
| Test | `tests/integration/sql_postgres/` | Testy integracyjne Postgres |
| Test | `tests/e2e/api/` | Testy E2E API |
| Test | `tests/e2e/cli/` | Testy E2E CLI |
| Test | `tests/architecture/` | Testy architektury |

## Ograniczenia

- Nazwy katalogów zawsze w liczbie mnogiej (wyjątek: nazwy agregatów)
- `snake_case` — małe litery, podkreślenia
- Jeden poziom zagłębienia dla encji/eventów/VO wewnątrz agregatu
- Żadnych skrótów w nazwach katalogów
