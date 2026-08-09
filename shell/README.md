# shell — Przewodnik po projekcie

`shell` to platforma SHELL w architekturze DDD + Hexagonal + CQRS, podzielona na Bounded Contexty.

---

## Spis treści

1. [Instalacja i wymagania](#1-instalacja-i-wymagania)
2. [Zmienne środowiskowe](#2-zmienne-środowiskowe)
3. [Uruchamianie — CLI](#3-uruchamianie--cli)
4. [Uruchamianie — FastAPI](#4-uruchamianie--fastapi)
5. [Narzędzia administracyjne (bootstrap/main.py)](#5-narzędzia-administracyjne-bootstrapmainpy)
6. [Testowanie](#6-testowanie)
7. [Architektura warstwowa](#7-architektura-warstwowa)
8. [Bounded Contexty](#8-bounded-contexty)
9. [Mapa plików — co gdzie jest](#9-mapa-plików--co-gdzie-jest)
10. [Agregaty i ich relacje](#10-agregaty-i-ich-relacje)
11. [Szyny (CommandBus / QueryBus / EventBus)](#11-szyny-commandbus--querybus--eventbus)
12. [Persistence — adaptery bazodanowe](#12-persistence--adaptery-bazodanowe)
13. [Observability](#13-observability)

---

## 1. Instalacja i wymagania

**Python 3.11+** wymagany.

```powershell
# z katalogu głównego repo (SHELL/)
pip install -e "shell[dev]"
```

Zależności produkcyjne (z `shell/pyproject.toml`):

| Pakiet | Do czego |
|---|---|
| `fastapi`, `uvicorn` | REST API (control plane) |
| `sqlalchemy>=2.0` | ORM async (SQLite + Postgres) |
| `aiosqlite` | SQLite async driver |
| `asyncpg` | PostgreSQL async driver |
| `alembic` | Migracje schematu SQL |
| `pydantic>=2.7`, `pydantic-settings` | DTO, Settings, request/response modele |
| `dependency-injector` | DI per BC — **legacy, tylko w martwych kontenerach** (patrz `do_usuniecia.md`); composition root używa Pure DI |
| `motor` | MongoDB async driver (adapter zawieszony) |
| `pyyaml` | Parsowanie task.yaml |
| `httpx` | Klient HTTP/testy e2e |
| `apscheduler` | Scheduled job execution |

Zależności dev (`[dev]`): `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff`, `import-linter`.

---

## 2. Zmienne środowiskowe

Wszystkie mają wartości domyślne — projekt działa bez ustawiania czegokolwiek.

| Zmienna | Domyślna wartość | Opis |
|---|---|---|
| `shell_DATABASE_URL` | `sqlite+aiosqlite:///shell.db` | URL bazy danych; zmień na `postgresql+asyncpg://...` dla Postgres |
| `shell_MAX_STEP` | `20` | Maksymalna liczba kroków routingu w jednym przebiegu |
| `shell_MAX_PARALLEL` | `4` | Liczba równoległych node'ów w `run-tasker` |
| `PG_TEST_URL` | *(brak)* | URL Postgres dla testów integracyjnych; testy są pomijane gdy nie ustawione |

Ustawianie w PowerShell (tymczasowo na czas sesji):

```powershell
$env:shell_DATABASE_URL = "sqlite+aiosqlite:///moja_baza.db"
$env:shell_MAX_STEP = "50"
```

Ustawianie dla Postgres:

```powershell
$env:shell_DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/shell"
```

---

## 3. Uruchamianie — CLI

Wszystkie komendy uruchamiane z **katalogu głównego repo** (`SHELL/`):

```powershell
python -m shell.framework.cli.main <subkomenda> [parametry]
```

### 3.1 `import-task` — importuj zadanie z pliku

Czyta parę plików `<task-name>.md` + `<task-name>.yaml` i zapisuje `Task` do bazy.

```powershell
python -m shell.framework.cli.main import-task `
    --task-name my-task `
    --task-dir ./workplace/example_tasks/
```

| Parametr | Wymagany | Opis |
|---|---|---|
| `--task-name NAME` | tak | Nazwa zadania (bez rozszerzenia); szuka `<task-dir>/<NAME>.md` i `.yaml` |
| `--task-dir PATH` | tak | Katalog z plikami `.md` i `.yaml` |

Wynik: wypisuje `Imported task 'my-task' with id=<uuid>`.

---

### 3.2 `route` — uruchom routing workflow

Przetwarza oczekujące koperty (`Envelope`) dla danego workflow.

```powershell
python -m shell.framework.cli.main route `
    --workflow-id <uuid>
```

| Parametr | Wymagany | Opis |
|---|---|---|
| `--workflow-id ID` | nie | UUID workflow; domyślnie `"default"` |
| `--max-step N` | nie | Nadpisuje `shell_MAX_STEP` |

Wynik: `Routed N envelopes.`

---

### 3.3 `run-tasker` — pełny cykl orchestracji

Importuje zadanie (jeśli nie istnieje), uruchamia workflow i wykonuje wszystkie node'y w grafie.

```powershell
python -m shell.framework.cli.main run-tasker `
    --task-name my-task `
    --work-dir ./work/
```

| Parametr | Wymagany | Opis |
|---|---|---|
| `--task-name NAME` | tak | Nazwa zaimportowanego zadania |
| `--work-dir PATH` | nie | Katalog roboczy node'ów; domyślnie CWD |

Wynik: `Tasker workflow completed: workflow_id=<uuid>`

---

### 3.4 `agent` / `router` / `tasker` / `tool` / `worker` — uruchamianie pojedynczego node'a

Wywołania odpowiadające starym entrypointom (CLI parity):

```powershell
python -m shell.framework.cli.main agent `
    --node-dir ./work/agent-01 `
    --workflow-id <uuid> `
    --work-dir ./work/
```

Wszystkie tryby przyjmują ten sam zestaw flag (zdefiniowany w `framework/cli/parser.py`):

| Parametr | Opis |
|---|---|
| `--node-dir PATH` | Katalog konkretnego node'a |
| `--workflow-id ID` | UUID workflow |
| `--work-dir PATH` | Katalog roboczy |
| `--max-step N` | Max kroków routingu |
| `--mode MODE` | Tryb wykonania (agent/router/tasker/tool/worker) |
| `--role ROLE` | Rola node'a |
| `--model MODEL` | Model LLM |
| `--timeout SECONDS` | Timeout wykonania |
| `--dry-run` | Symulacja bez zapisu |
| `--log-level LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR` (domyślnie `INFO`) |
| `--prompt PROMPT` | Treść promptu |
| `--prompt-dir PATH` | Katalog z plikami promptów |
| `--autopilot` | Tryb autopilota (bez pytania użytkownika) |
| `--no-ask-user` | Wyłącza interakcję z użytkownikiem |
| `--add-dir PATH` | Dodatkowy katalog (można podać wielokrotnie) |

---

## 4. Uruchamianie — FastAPI

FastAPI to **control plane** — zarządzanie taskami i workflow przez HTTP.  
Każdy Bounded Context wystawia własną aplikację FastAPI.

### Uruchomienie serwera dla konkretnego BC

```powershell
python -c "
import asyncio, uvicorn
from shell.bootstrap.execution.factory.application_factory import ApplicationFactory
from shell.framework.user.api.app import create_user_app
from shell.platform.infrastructure.configuration.shell_config import ShellConfig

async def main():
    config = ShellConfig.from_environment()
    container = await ApplicationFactory(config).build()
    app = create_user_app(container)
    uvicorn_config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(uvicorn_config)
    await server.serve()

asyncio.run(main())
"
```

Pełny entrypoint (monolit): `python -m shell.platform.framework.api`.

### Endpointy per BC

| BC | App factory | Ścieżki |
|---|---|---|
| **user** | `create_user_app()` | `/users/**`, `/health` |
| **session** | `create_session_app()` | `/sessions/**` |
| **definition** | `create_definition_app()` | `/definitions/**` |
| **execution** | `create_execution_app()` | `/workflows/**`, `/nodes/**` |
| **project** | `create_project_app()` | `/projects/**` |

Dokumentacja Swagger dostępna pod: `http://localhost:8000/docs`

---

## 5. Narzędzia administracyjne (bootstrap/main.py)

```powershell
python -m shell.platform.bootstrap.main <komenda> [--db-url URL]
```

| Komenda | Opis |
|---|---|
| `smoke` | Import → workflow → route na tymczasowej bazie SQLite. Sprawdza czy cały stos działa. |
| `relay` | Przetwarza jeden batch oczekujących wpisów w tabeli `outbox_event` i publikuje je downstream. |

```powershell
# Smoke test na domyślnej bazie
python -m shell.platform.bootstrap.main smoke

# Smoke test na konkretnej bazie
python -m shell.platform.bootstrap.main smoke --db-url sqlite+aiosqlite:///moja_baza.db

# Przetworz outbox na bazie Postgres
python -m shell.platform.bootstrap.main relay --db-url "postgresql+asyncpg://user:pass@localhost/shell"
```

---

## 6. Testowanie

### Uruchamianie testów

```powershell
# Wszystkie testy (z katalogu SHELL/)
python -m pytest shell/tests -x

# Tylko unit testy (szybkie, bez I/O)
python -m pytest shell/tests -x -k "unit"

# Tylko integracyjne SQLite
python -m pytest shell/tests/integration/sql_sqlite -x

# Testy architektury (sprawdza konwencje warstw, nazewnictwo, strukture)
python -m pytest shell/tests/architecture -x

# Testy dla konkretnego BC
python -m pytest shell/tests/user -x
python -m pytest shell/tests/execution -x

# Z pokryciem kodu
python -m pytest shell/tests --cov=shell --cov-report=term-missing
```

### Lint i typy

```powershell
# Ruff — linter (całe shell)
python -m ruff check shell

# Ruff z auto-fixem
python -m ruff check shell --fix

# MyPy — strict dla domain i application
python -m mypy --strict shell/domain shell/application

# MyPy bez strict dla reszty
python -m mypy shell/infrastructure shell/framework shell/bootstrap
```

### Struktura testów

```
shell/tests/
├── architecture/               ← 19 testów: AST scanner, import-linter, nazewnictwo
├── user/                       ← Testy BC user
│   ├── unit/
│   └── user/
├── session/                    ← Testy BC session
├── execution/                  ← Testy BC execution
│   ├── unit/
│   ├── integration/
│   └── e2e/
├── definition/                 ← Testy BC definition
├── messaging/                  ← Testy BC messaging
├── project/                    ← Testy BC project
├── scheduling/                 ← Testy BC scheduling
├── platform/                   ← Testy warstwy platform (buses, middleware)
├── process/                    ← Testy procesów/sag
├── infrastructure/             ← Testy infrastruktury
└── shared/                     ← Wspólne test doubles, helpery
```

---

## 7. Architektura warstwowa

```
domain ← application ← infrastructure ← framework
                                                    ↕
                                              bootstrap
                                              platform
                                              process
```

Importy idą **tylko w tym kierunku** — żadna niższa warstwa nie może importować z wyższej. Egzekwowane przez `import-linter` i testy architektury.

| Warstwa | Co zawiera | Dozwolone importy |
|---|---|---|
| `domain/` | Agregaty, encje, VO, eventy domenowe, porty repozytoriów, wyjątki | Tylko stdlib |
| `application/` | Komendy, zapytania, handlery (CQRS), DTO, porty aplikacyjne | `domain/` + stdlib |
| `infrastructure/` | Adaptery SQL/Memory/HTTP, modele ORM, mappery, logging, messaging | `domain/` + `application/` + libs |
| `framework/` | CLI (argparse), FastAPI per BC | `infrastructure/` (przez DI) |
| `bootstrap/` | Composition Root (Pure DI `Container`), `ApplicationFactory` | Wszystkie warstwy |
| `platform/` | Shared Kernel: klasy bazowe, busy, shared VOs, persistence base | Tylko stdlib + libs |
| `process/` | Sagi / Process Managery (long-running workflows) | `domain/` + `application/` |

**Każda warstwa dzieli się na Bounded Contexty** — nie ma płaskiej struktury.

---

## 8. Bounded Contexty

| BC | domain/aggregates | application/ | infrastructure/ | framework/ | bootstrap/ |
|---|---|---|---|---|---|
| **user** | user, user_state, user_skill | commands, queries, handlers | SQL repos, HTTP adapters | FastAPI router | (przez CoreContainer) |
| **session** | session, session_state | commands, queries | SQL repos | FastAPI router | (przez CoreContainer) |
| **definition** | graph_definition, node_definition, runner_config, graph_definition_embedding | queries | SQL repos | FastAPI router | (przez CoreContainer) |
| **execution** | workflow, graph_execution, node_execution, edge_execution, task_execution, session_execution i in. (19 agregatów) | commands, queries per agregat | SQL repos per agregat | FastAPI router + orchestration | (przez CoreContainer) |
| **messaging** | message_router | queries | SQL repos | — | (przez CoreContainer) |
| **project** | project, project_skill, project_state | commands, queries | SQL repos, HTTP | FastAPI router | (przez CoreContainer) |
| **scheduling** | scheduler_definition, scheduler_execution, scheduler_job | queries | SQL repos, services | — | (przez CoreContainer) |

---

## 9. Mapa plików — co gdzie jest

### Struktura per-BC (wzorzec)

Każdy Bounded Context powtarza tę samą strukturę we wszystkich warstwach:

```
domain/<bc>/
└── aggregates/
    └── <aggregate>/
        ├── <aggregate>.py          ← AggregateRoot
        ├── entities/               ← Child encje (jeśli istnieją)
        ├── events/                 ← Eventy domenowe
        ├── exceptions/             ← Wyjątki domenowe
        ├── ports/                  ← Porty (Protocol)
        ├── repositories/           ← Interfejsy repozytoriów (Protocol)
        └── value_objects/          ← Value Objecty

application/<bc>/
├── commands/                       ← Commandy (frozen dataclass)
├── command_handlers/               ← Handlery komend
├── queries/                        ← Zapytania (frozen dataclass)
├── query_handlers/                 ← Handlery zapytań
├── dto/                            ← DTO (frozen dataclass, primitives only)
├── ports/                          ← Porty aplikacyjne (Protocol)
├── mappers/                        ← Entity ↔ DTO
├── event_handlers/                 ← Handlery eventów domenowych
└── exceptions/                     ← Wyjątki aplikacyjne

infrastructure/<bc>/
├── <aggregate>/
│   └── persistence/
│       ├── sql/
│       │   ├── models/            ← SQLAlchemy ORM modele
│       │   ├── repositories/      ← Implementacje SQL repozytoriów
│       │   └── mappers.py         ← Entity ↔ Model
│       └── memory/                ← InMemory (testy)
├── http/                           ← Adaptery HTTP (cross-BC)
└── services/                       ← Serwisy infrastrukturalne

framework/<bc>/
└── api/
    ├── app.py                      ← FastAPI app factory
    ├── router.py                   ← Router
    └── middleware/                  ← Middleware (jeśli BC-specific)

bootstrap/<bc>/
└── container/
    └── <bc>_container.py           ← DI Container per BC (legacy, martwy — do usunięcia)
```

### platform/ — Shared Kernel

```
platform/
├── domain/base/                    ← AggregateRoot, Entity, EntityId, ValueObject
├── domain/events/                  ← DomainEvent, AggregateDeletedEvent
├── domain/exceptions/              ← DomainError
├── domain/ports/                   ← RepositoryPort (generic Protocol)
├── domain/value_objects/           ← Shared VOs (CreatedAt, UpdatedAt itp.)
├── application/bus/                ← CommandBus, QueryBus, EventBus, MessageBus
├── application/context/            ← CorrelationId, CausationId
├── application/exceptions/         ← ApplicationError
├── application/ports/              ← UnitOfWork, Clock, IdGenerator itp.
├── infrastructure/persistence/     ← SQLAlchemy Base, session factory, UoW base, migracje
├── infrastructure/identity/        ← UUID id generator
├── infrastructure/logging/         ← StdlibLogger (JSON, correlation_id)
├── infrastructure/messaging/       ← Outbox/Inbox relay
├── infrastructure/time/            ← SystemClock
├── infrastructure/serialization/   ← Domain event serializer
├── infrastructure/configuration/   ← YAML config loader
├── framework/api/                  ← Wspólne: middleware, OpenAPI, websocket
├── framework/cli/                  ← Wspólny parser CLI
├── bootstrap/container/            ← Composition Root — Pure DI (Container + moduły)
└── bootstrap/config_logging/       ← Konfiguracja logowania
```

### Composition Root (Pure DI) — `platform/bootstrap/container/`

Cały DI jest ręcznie spięty w **jednym Composition Root** bez frameworka DI
(`dependency-injector` nie jest używany w kodzie produkcyjnym — patrz `do_usuniecia.md`).

```
platform/bootstrap/container/
├── root.py                     ← Container / CoreContainer — kompozycja warstw (entrypoint)
├── infrastructure.py           ← Infrastructure — session_factory, query services, UoW factory, publisherowie
├── buses.py                    ← Buses — CommandBus, QueryBus, EventBus, MessageBus
├── application.py              ← Application — komponuje buses, commands, queries, event_handlers
├── command_factories.py        ← Commands — fabryki command handlerów
├── query_factories.py          ← Queries — fabryki query handlerów
├── event_handlers.py           ← EventHandlers — fabryki event handlerów
├── events.py                   ← Events — outbox/inbox relay i procesory
├── execution_command_factories.py    ← mixin fabryk handlerów BC execution
├── scheduling_command_factories.py   ← mixin fabryk handlerów BC scheduling
└── core_container.py           ← re-eksport kompatybilności (Container, CoreContainer, ...)

platform/bootstrap/factory/
├── bus_factory.py              ← wire_buses(container) — spina rejestrację wszystkich busów
├── command_factory.py          ← register_commands(container)
├── query_factory.py            ← register_queries(container)
├── event_factory.py            ← register_events(container)
└── message_factory.py          ← register_messages(container)
```

Cykl życia: `Singleton` = obiekty współdzielone (busy, query services), `transient` = nowa
instancja przy każdym wywołaniu fabryki (handlery, UoW, mapper). Semantyka transient jest
zachowana przez fabryki (`unit_of_work_factory()`, `clock_factory()`, `id_generator_factory()`).

---

## 10. Agregaty i ich relacje

```mermaid
graph TD
    User -->|ma| UserState
    User -->|ma| UserSkill
    Session -->|należy do| User
    Session -->|zawiera| Message
    Task -->|ma| Graph
    Graph -->|zawiera| Node
    Workflow -->|śledzi| NodeState
    Workflow -->|powiązany z| Task
    Workflow -->|ma| GraphExecution
    GraphExecution -->|zawiera| NodeExecution
    NodeExecution -->|ma| EdgeExecution
    EdgeExecution -->|łączy| NodeExecution
    Envelope -->|należy do| Workflow
    Envelope -->|dotyczy| Node
    NodeResult -->|wynik| Envelope
    Project -->|zawiera| ProjectSkill
    Project -->|ma| ProjectState
    SchedulerDefinition -->|tworzy| SchedulerJob
    SchedulerJob -->|uruchamia| SchedulerExecution
    MessageRouter -->|przetwarza| Message
```

---

## 11. Szyny (CommandBus / QueryBus / EventBus)

Wszystkie busy zdefiniowane w `platform/application/bus/`, instantowane jako singlety w
`Buses` (`platform/bootstrap/container/buses.py`) i dostępne przez `container.app.buses`.

### Rejestracja handlerów

Handlery są rejestrowane **deklaratywnie w fabrykach rejestracji**
(`platform/bootstrap/factory/*.py`), a instancje tworzone przez fabryki handlerów
w `container.app.commands` / `container.app.queries` / `container.app.event_handlers`:

```python
# platform/bootstrap/factory/command_factory.py
def register_commands(container: Container) -> None:
    cmd_bus = container.app.buses.command_bus
    commands = container.app.commands
    cmd_bus.register(CreateUserCommand, commands.create_user_handler_factory)
```

Pełne spięcie robi `wire_buses(container)` (`bus_factory.py`), wywoływane przez
`ApplicationFactory.build()`.

### Wywołanie z kodu

```python
# Command (zapis stanu)
command_bus = container.app.buses.command_bus
user_id: UserId = await command_bus.dispatch(
    CreateUserCommand(email="user@example.com", name="John")
)

# Query (odczyt bez efektów ubocznych)
query_bus = container.app.buses.query_bus
dto: UserDto | None = await query_bus.dispatch(
    GetUserQuery(user_id=user_id)
)
```

---

## 12. Persistence — adaptery bazodanowe

### Tabele SQL (per BC)

| BC | Tabele |
|---|---|
| **user** | `user`, `user_state`, `user_skill` |
| **session** | `session`, `message` |
| **definition** | `graph_definition`, `node_definition`, `node_link_definition`, `runner_config`, `graph_definition_embedding` |
| **execution** | `workflow`, `graph_execution`, `node_execution`, `edge_execution`, `session_execution`, `task_execution`, `envelope`, `node_result`, `prompt` |
| **project** | `project`, `project_skill`, `project_state` |
| **scheduling** | `scheduler_definition`, `scheduler_job`, `scheduler_execution` |
| **messaging** | `message_router`, `inbox_message`, `outbox_message` |
| **platform** | `audit_event`, `outbox_event` |

### Migracje

Migracje Alembic: `platform/infrastructure/persistence/migrations/sql/versions/` (56 migracji).

### Unit of Work

Każdy BC ma własną implementację UoW (np. `SqlAlchemyUserUnitOfWork`), która zarządza transakcjami i outboxem dla swojego BC. Wszystkie dziedziczą po `SqlAlchemyUnitOfWorkBase` z `platform/infrastructure/persistence/`.

### Zmiana backendu

```powershell
# SQLite (domyślny, bez konfiguracji)
$env:shell_DATABASE_URL = "sqlite+aiosqlite:///shell.db"

# PostgreSQL
$env:shell_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/shell_db"
```

---

## 13. Observability

### Logi (JSON)

`StdlibLogger` wypisuje każdy log jako jednolinijkowy JSON na stdout:

```json
{"ts": "2025-01-15T10:23:45.123456", "level": "INFO", "logger": "shell", "msg": "domain_event", "event_type": "TaskImported", "correlation_id": "abc-123"}
```

Correlation ID jest propagowane przez `contextvars` — ustawiane automatycznie przez `CorrelationIdMiddleware` (API) lub można je ustawić ręcznie:

```python
from shell.infrastructure.logging.stdlib_logger import set_correlation_id
set_correlation_id("moj-request-id")
```

### Tabela audit_event

Każdy opublikowany event domenowy trafia do tabeli `audit_event` (przez `SqlAuditPublisher`).  
Kolumny: `id`, `event_type`, `occurred_at`, `payload` (JSON).

### Tabela outbox_event

`SqlEventOutboxPublisher` zapisuje eventy do `outbox_event` z `published_at = NULL`.  
`EventOutboxToInboxRelay.run_once()` pobiera niepublikowane wpisy i przekazuje je do `inbox_event`, ustawiając `published_at`.

```powershell
# Uruchom relay ręcznie
python -m shell.platform.bootstrap.main relay --db-url sqlite+aiosqlite:///shell.db
```
