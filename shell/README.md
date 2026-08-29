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
| `dependency-injector` | Kontenery DI poszczególnych BC |
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
python -m shell.platform.framework.cli.main <subkomenda> [parametry]
```

### 3.1 `import-task` — importuj zadanie z pliku

Czyta parę plików `<task-name>.md` + `<task-name>.yaml` i zapisuje `Task` do bazy.

```powershell
python -m shell.platform.framework.cli.main import-task `
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
python -m shell.platform.framework.cli.main route `
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
python -m shell.platform.framework.cli.main run-tasker `
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
python -m shell.platform.framework.cli.main agent `
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
from shell.user_service.bootstrap.user.container.user_core_container import (
    UserCoreContainer,
    configure_user_container,
)
from shell.user_service.framework.user.api.app import create_user_app

async def main():
    container = UserCoreContainer()
    configure_user_container(container)
    app = create_user_app(container)
    uvicorn_config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(uvicorn_config)
    await server.serve()

asyncio.run(main())
"
```

Każdy BC uruchamia się własnym entrypointem i własną bazą danych.

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

## 5. Narzędzia administracyjne

```powershell
python -m shell.execution_service.bootstrap.execution.main --port 8000
```

| Komenda | Opis |
|---|---|
| `execution` | Uruchamia wyłącznie Execution BC. |
| `session` | Uruchamia wyłącznie Session BC. |
| `user` | Uruchamia wyłącznie User BC. |

```powershell
# Każdy proces uruchamia jeden bounded context
python -m shell.execution_service.bootstrap.execution.main --port 8000
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
python -m mypy shell/infrastructure shell/framework
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
├── ingestion/                  ← Testy BC ingestion
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
| `bootstrap/` | Composition Root konkretnego BC | Wszystkie warstwy tego BC |
| `platform/` | Shared Kernel: klasy bazowe, busy, shared VOs, persistence base | Tylko stdlib + libs |
| `process/` | Sagi / Process Managery (long-running workflows) | `domain/` + `application/` |

**Każda warstwa dzieli się na Bounded Contexty** — nie ma płaskiej struktury.

---

## 8. Bounded Contexty

| BC | domain/aggregates | application/ | infrastructure/ | framework/ | bootstrap/ |
|---|---|---|---|---|---|
| **user** | user, user_state, user_skill | commands, queries, handlers | SQL repos, HTTP adapters | FastAPI router | `UserCoreContainer` |
| **session** | session, session_state | commands, queries | SQL repos | FastAPI router | `SessionCoreContainer` |
| **definition** | graph_definition, node_definition, runner_config, graph_definition_embedding | queries | SQL repos | FastAPI router | `DefinitionCoreContainer` |
| **execution** | workflow, graph_execution, node_execution, edge_execution, task_execution, session_execution i in. (19 agregatów) | commands, queries per agregat | SQL repos per agregat | FastAPI router + orchestration | `ExecutionCoreContainer` |
| **ingestion** | ingestion | queries, commands | SQL repos | FastAPI router | `IngestionCoreContainer` |
| **project** | project, project_skill, project_state | commands, queries | SQL repos, HTTP | FastAPI router | `ProjectCoreContainer` |
| **scheduling** | scheduler_definition, scheduler_execution, scheduler_job | queries | SQL repos, services | — | `SchedulingCoreContainer` |

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
    └── <bc>_core_container.py      ← kontener DI konkretnego BC
```

### platform/ — Shared Kernel

```
platform/
├── domain/base/                    ← AggregateRoot, Entity, EntityId, ValueObject
├── domain/events/                  ← DomainEvent, AggregateDeletedEvent
├── domain/exceptions/              ← DomainError
├── domain/ports/                   ← RepositoryPort (generic Protocol)
├── domain/value_objects/           ← Shared VOs (CreatedAt, UpdatedAt itp.)
├── application/bus/                ← CommandBus, QueryBus, EventBus
├── application/context/            ← CorrelationId, CausationId
├── application/exceptions/         ← ApplicationError
├── application/ports/              ← UnitOfWork, Clock, IdGenerator itp.
├── observability/                  ← Capability: metryki, readiness, ekspozycja (ADR-0002)
│   ├── application/ports/          ← MetricsBackend, MetricsExporter, ReadinessProbe
│   ├── infrastructure/metrics/     ← MetricsRegistry, Logging/Prometheus backends
│   ├── infrastructure/health/      ← Composite/Rabbit/Sql readiness probes
│   └── framework/api/              ← /metrics, /readiness, MetricsMiddleware, mount_*
├── infrastructure/persistence/     ← SQLAlchemy Base, session factory, UoW base, migracje
├── infrastructure/identity/        ← UUID id generator
├── infrastructure/logging/         ← StdlibLogger (JSON, correlation_id)
├── infrastructure/messaging/       ← Outbox/Inbox relay
├── infrastructure/time/            ← SystemClock
├── infrastructure/serialization/   ← Domain event serializer
├── infrastructure/configuration/   ← YAML config loader
├── framework/api/                  ← Wspólne: middleware, OpenAPI, websocket
├── framework/cli/                  ← Wspólny parser CLI
└── bootstrap/config_logging/       ← Konfiguracja logowania
```

### Composition Roots per BC

Każdy bounded context ma własny composition root i nie współdzieli kontenera z innym BC.
Platforma dostarcza generyczne busy, persistence, serializację oraz wzorzec inbox/outbox;
konkretne modele event delivery są instalowane w metadata danego BC.

```
shell/<bc>/bootstrap/<bc>/
├── main.py                     ← entrypoint usługi BC
├── event_registry.py           ← rejestr własnych eventów BC
└── container/<bc>_core_container.py
                                  ← kontener wyłącznie tego BC
```

Komunikacja między BC odbywa się wyłącznie przez publiczne kontrakty HTTP lub eventowe.

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
    Ingestion -->|przetwarza| Message
```

---

## 11. Szyny (CommandBus / QueryBus / EventBus)

Wszystkie busy są zdefiniowane w `platform/application/bus/` i konfigurowane lokalnie
w kontenerze konkretnego BC; nie istnieje wspólny bus/container dla wszystkich BC.

### Rejestracja handlerów

Handlery są rejestrowane w konfiguracji kontenera konkretnego BC, na przykład
w `shell/user_service/bootstrap/user/container/user_core_container.py`.

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
| **ingestion** | `ingestion`, `outbox_event`, `inbox_event`, `outbox_command`, `inbox_command`, `audit_event` |
| **pozostałe BC** | własne tabele domenowe oraz te same lokalne tabele delivery |

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

Mechanizmy obserwowalności to wspólna zdolność platformy w
`shell/platform/observability/` (ADR-0002): metryki, readiness i logowanie.
Szczegóły w Wiki `shell/platform/doc/`: [metrics](platform/doc/metrics.md),
[readiness](platform/doc/readiness.md), [logging](platform/doc/logging.md),
[tracing-context](platform/doc/tracing-context.md).

### Metryki (Prometheus, `/metrics`)

Każdy serwis eksponuje `GET /metrics` w formacie Prometheus
(`text/plain; version=0.0.4`) — rejestr, backendy i middleware w
`shell/platform/observability/`. Decyzja o własnym rejestrze: ADR-0003.

```powershell
# Przykładowy scrape
curl http://127.0.0.1:8000/metrics
```

Metryki platformowe obejmują HTTP (inbound/outbound), retry, circuit breaker
oraz backlog inbox/outbox. Szczegóły: [metrics](platform/doc/metrics.md).

### Readiness (`/readiness`)

Serwis jest gotowy, gdy DB, migracje, worker i broker (RabbitMQ) działają.
`GET /readiness` zwraca 200 z `status=ready` albo 503 z diagnostycznym ciałem.
Healthchecki produkcyjne (docker-compose) wołają `/readiness`; `/health`
pozostaje sygnałem liveness.

### Logi (JSON)

`StdlibLogger` wypisuje każdy log jako jednolinijkowy JSON na stdout:

```json
{"ts": "2025-01-15T10:23:45.123456", "level": "INFO", "logger": "shell", "msg": "domain_event", "event_type": "TaskImported", "correlation_id": "abc-123"}
```

Correlation ID jest propagowane przez `contextvars` — ustawiane automatycznie przez `CorrelationIdMiddleware` (API) lub można je ustawić ręcznie:

```python
from shell.platform.infrastructure.logging.stdlib_logger import set_correlation_id
set_correlation_id("moj-request-id")
```

### Tabela audit_event

Każdy opublikowany event domenowy trafia do tabeli `audit_event` (przez `SqlAuditPublisher`).  
Kolumny: `id`, `event_type`, `occurred_at`, `payload` (JSON).

### Tabela outbox_event

`SqlAlchemyUnitOfWorkBase` zapisuje event oraz `outbox_event` atomowo.  
`OutboxToTransportRelay.run_once()` publikuje nieopublikowane koperty przez broker, a docelowy `RabbitInboxConsumer` zapisuje je do lokalnego `inbox_event`.

```powershell
# Relay uruchamiany jest przez proces właściwego BC
python -m shell.execution_service.bootstrap.execution.cli.command.relay_command
```
