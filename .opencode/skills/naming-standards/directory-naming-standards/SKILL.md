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

> SHELL nie ma top-level pakietów `domain/`, `application/`, `infrastructure/`, `framework/`, `bootstrap/`. Realna struktura to `shell/<service>/{domain,application,process,infrastructure,framework,bootstrap}/<bc>/...` (np. `shell/execution_service/domain/execution/...`) oraz platforma `shell/platform/...`.

| Warstwa | Katalog | Zawartość |
|---------|---------|-----------|
| Domain (platforma) | `shell/platform/domain/base/` | Entity/AggregateRoot/ValueObject/EntityId base classes |
| Domain (platforma) | `shell/platform/domain/value_objects/` | Uniwersalne VO platformy |
| Domain (platforma) | `shell/platform/domain/ports/` | Porty platformy (Clock, IdGenerator, RepositoryPort) |
| Domain (platforma) | `shell/platform/domain/events/` | DomainEvent base class |
| Domain (platforma) | `shell/platform/domain/exceptions/` | DomainError base |
| Domain | `shell/<service>/domain/<bc>/aggregates/<nazwa_agregatu>/` | Aggregate Root |
| Domain | `.../aggregates/<nazwa_agregatu>/entities/` | Child entities |
| Domain | `.../aggregates/<nazwa_agregatu>/events/` | Domain Events |
| Domain | `.../aggregates/<nazwa_agregatu>/value_objects/` | Value Objects (w tym ID) |
| Domain | `.../aggregates/<agregat>/repositories/` | Porty repozytoriów per agregat |
| Domain | `.../aggregates/<agregat>/services/` | Domain Services per agregat |
| Domain | `.../aggregates/<agregat>/exceptions/` | Domain Exceptions per agregat |
| Domain | `.../aggregates/<agregat>/ports/` | Porty domenowe (Provider / Command Port) per agregat |
| Application | `.../application/<bc>/<aggregate>/commands/` | Komendy per agregat |
| Application | `.../application/<bc>/<aggregate>/command_handlers/` | Handlery komend per agregat |
| Application (platforma) | `shell/platform/application/commands/` + `command_handlers/` | Komendy i handlery platformy (siblings, liczba mnoga) |
| Application (platforma) | `shell/platform/application/events/` + `event_handlers/` | Integracyjne eventy i ich handlery (siblings, liczba mnoga) |
| Application | `.../application/<bc>/<aggregate>/queries/` | Query per agregat |
| Application | `.../application/<bc>/<aggregate>/query_handlers/` | Handlery query per agregat |
| Application | `.../application/<bc>/<aggregate>/dto/` | DTO odpowiedzi per agregat |
| Application | `.../application/<bc>/<aggregate>/integration_events/` | Integration Events per agregat |
| Application | `.../application/<bc>/<aggregate>/ports/` | QueryServices i porty aplikacyjne per agregat |
| Application | `.../application/<bc>/<aggregate>/mappers/` | Mappery aplikacyjne (domain ↔ DTO) |
| Application | `.../application/<bc>/<aggregate>/sagas/` | Sagi per agregat |
| Infrastructure | `shell/<service>/infrastructure/<bc>/<aggregate>/persistence/sql/repositories/` | SQL repozytoria per agregat |
| Infrastructure | `.../infrastructure/<bc>/<aggregate>/persistence/memory/` | InMemory repozytoria per agregat |
| Infrastructure | `.../infrastructure/<bc>/<aggregate>/persistence/sql/models/` | ORM modele per agregat |
| Infrastructure | `.../infrastructure/<bc>/<aggregate>/persistence/sql/mappers/` | Mappery ORM per agregat |
| Infrastructure | `.../infrastructure/<bc>/<aggregate>/adapters/` | Adaptery portów (Provider / Command Port) |
| Infrastructure (platforma) | `shell/platform/infrastructure/...` | Adaptery uniwersalne (zegar, identity, outbox/inbox) |
| Framework | `shell/<service>/framework/<bc>/<aggregate>/api/` | Routery FastAPI per agregat |
| Process | `shell/<service>/process/<bc>/<nazwa_sagi>/` | Saga state machine (wzorzec docelowy) |
| Bootstrap | `shell/<service>/bootstrap/<bc>/container/` | DI per BC (np. `<bc>_core_container.py`) |
| Test | `shell/tests/<bc_service>/unit/` | Testy jednostkowe per BC |
| Test | `shell/tests/<bc_service>/integration/sql_sqlite/` | Testy integracyjne SQLite per BC |
| Test | `shell/tests/<bc_service>/integration/sql_postgres/` | Testy integracyjne Postgres per BC |
| Test | `shell/tests/<bc_service>/e2e/api/` | Testy E2E API per BC |
| Test | `shell/tests/architecture/` | Testy architektury (flat) |
| Test | `shell/tests/contracts/` | Publiczne kontrakty HTTP/event między BC |

> **Szczegółowe reguły → [naming-convention-standard](../naming-convention-standard/SKILL.md)**

## Zasada rodzeństwa (siblings) — pojęcie i jego handlery na tym samym poziomie

Katalog pojęcia i katalog jego handlerów są **rodzeństwem na tym samym poziomie**,
zawsze w **liczbie mnogiej**:

```
…/commands/          +  …/command_handlers/
…/queries/           +  …/query_handlers/
…/events/            +  …/event_handlers/
…/integration_events/ + …/event_handlers/
```

**Zakazane kształty:**
- **NIE wolno zagnieżdżać handlerów pod pojęciem**: `…/command/handlers/`,
  `…/event/handlers/` — handlery idą obok, nie pod spodem.
- **NIE wolno liczby pojedynczej**: `command/`, `command_handler/`,
  `event/`, `event_handler/` — liczba mnoga: `commands/`, `command_handlers/`,
  `events/`, `event_handlers/`.

Obowiązuje w platformie i w BC:
- `shell/platform/application/` → `commands/` + `command_handlers/`,
  `events/` + `event_handlers/` (platforma zrefaktorowana: dawna `command/handlers/`
  przeniesiona do `commands/` + `command_handlers/` + `event_handlers/`).
- `shell/<service>/application/<bc>/<aggregate>/` → `commands/` +
  `command_handlers/`, `integration_events/` + `event_handlers/`.

## Ograniczenia

- Nazwy katalogów zawsze w liczbie mnogiej (wyjątek: nazwy agregatów)
- `snake_case` — małe litery, podkreślenia
- Jeden poziom zagłębienia dla encji/eventów/VO wewnątrz agregatu
- Żadnych skrótów w nazwach katalogów
