# shell — Przewodnik po projekcie

`shell` to reimplementacja platformy SHELL w architekturze DDD + Hexagonal + CQRS.  
Stary katalog `shell/` pozostaje niezmieniony i służy jako referencja behawioralna.

---

## Spis treści

1. [Instalacja i wymagania](#1-instalacja-i-wymagania)
2. [Zmienne środowiskowe](#2-zmienne-środowiskowe)
3. [Uruchamianie — CLI](#3-uruchamianie--cli)
4. [Uruchamianie — FastAPI](#4-uruchamianie--fastapi)
5. [Narzędzia administracyjne (bootstrap/main.py)](#5-narzędzia-administracyjne-bootstrapMainpy)
6. [Testowanie](#6-testowanie)
7. [Architektura warstwowa](#7-architektura-warstwowa)
8. [Mapa plików — co gdzie jest](#8-mapa-plików--co-gdzie-jest)
9. [Agregaty i ich relacje](#9-agregaty-i-ich-relacje)
10. [Szyny (CommandBus / QueryBus / EventBus)](#10-szyny)
11. [Persistence — adaptery bazodanowe](#11-persistence--adaptery-bazodanowe)
12. [Observability](#12-observability)

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
| `motor` | MongoDB async driver (adapter zawieszony) |
| `pyyaml` | Parsowanie task.yaml |
| `httpx` | Klient HTTP w testach e2e |

Zależności dev (`[dev]`): `pytest`, `pytest-asyncio`, `pytest-cov`, `mypy`, `ruff`.

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
Nie zastępuje CLI dla wykonania node'ów; działa równolegle.

### Uruchomienie serwera

```powershell
# Najpierw zainicjuj kontener i podaj go do create_app
python -c "
import asyncio, uvicorn
from shell.bootstrap.container import ApplicationFactory
from shell.framework.api.app import create_app

async def main():
    container = await ApplicationFactory(database_url='sqlite+aiosqlite:///shell.db').build()
    app = create_app(container)
    config = uvicorn.Config(app, host='0.0.0.0', port=8000)
    server = uvicorn.Server(config)
    await server.serve()

asyncio.run(main())
"
```

### Endpointy

Dokumentacja Swagger dostępna pod: `http://localhost:8000/docs`

| Metoda | Ścieżka | Opis |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/tasks/import` | Import zadania |
| `GET` | `/tasks/{name}` | Pobierz task po nazwie |
| `POST` | `/workflows` | Utwórz nowy workflow |
| `GET` | `/workflows/{id}` | Pobierz status workflow |
| `POST` | `/workflows/{id}/route` | Uruchom routing |
| `GET` | `/workflows/{id}/envelopes` | Lista kopert workflow |
| `GET` | `/nodes/{id}/result` | Wynik wykonania node'a |

### Przykłady curl

```bash
# Import zadania
curl -X POST http://localhost:8000/tasks/import \
  -H "Content-Type: application/json" \
  -d '{"task_name":"my-task","md_path":"/path/to/my-task.md","yaml_path":"/path/to/my-task.yaml"}'

# Utwórz workflow
curl -X POST http://localhost:8000/workflows \
  -H "Content-Type: application/json" \
  -d '{"task_id":"task_id"}'

# Sprawdź status
curl http://localhost:8000/workflows/<workflow_id>

# Uruchom routing
curl -X POST http://localhost:8000/workflows/<workflow_id>/route
```

Każde żądanie dostaje nagłówek `X-Correlation-Id` (generowany automatycznie lub przekazany przez klienta).

---

## 5. Narzędzia administracyjne (bootstrap/main.py)

```powershell
python -m shell.bootstrap.main <komenda> [--db-url URL]
```

| Komenda | Opis |
|---|---|
| `smoke` | Import → workflow → route na tymczasowej bazie SQLite. Sprawdza czy cały stos działa. |
| `relay` | Przetwarza jeden batch oczekujących wpisów w tabeli `outbox_event` i publikuje je downstream. |

```powershell
# Smoke test na domyślnej bazie
python -m shell.bootstrap.main smoke

# Smoke test na konkretnej bazie
python -m shell.bootstrap.main smoke --db-url sqlite+aiosqlite:///moja_baza.db

# Przetworz outbox na bazie Postgres
python -m shell.bootstrap.main relay --db-url "postgresql+asyncpg://user:pass@localhost/shell"
```

---

## 6. Testowanie

### Uruchamianie testów

```powershell
# Wszystkie testy (z katalogu SHELL/)
python -m pytest shell/tests -x

# Tylko unit testy (szybkie, bez I/O)
python -m pytest shell/tests/unit -x

# Tylko integracyjne SQLite
python -m pytest shell/tests/integration/sql_sqlite -x

# Integracyjne Postgres (wymaga uruchomionego kontenera)
docker compose -f shell/docker-compose.test.yml up -d postgres
$env:PG_TEST_URL = "postgresql+asyncpg://shell:shell@localhost:5432/shell_test"
python -m pytest shell/tests/integration/sql_postgres -x
docker compose -f shell/docker-compose.test.yml down -v

# Testy e2e CLI
python -m pytest shell/tests/e2e/cli -x

# Testy e2e API (FastAPI TestClient)
python -m pytest shell/tests/e2e/api -x

# Architektura (sprawdza zakazy importów między warstwami)
python -m pytest shell/tests/architecture -x

# Z pokryciem kodu
python -m pytest shell/tests --cov=shell --cov-report=term-missing
```

### Flagi pytest

| Flaga | Opis |
|---|---|
| `-x` | Zatrzymaj po pierwszym błędzie |
| `-v` | Tryb verbose (lista wszystkich testów) |
| `-q` | Tryb cichy (tylko podsumowanie) |
| `--tb=short` | Krótki traceback (domyślnie `short`) |
| `-k "słowo"` | Uruchom tylko testy pasujące do wyrażenia, np. `-k "task"` |
| `--no-header` | Bez nagłówka pytest |

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

### Struktura testów i co gdzie pisać

```
shell/tests/
├── architecture/
│   └── test_imports.py          ← AST scanner: zakazy importów między warstwami
├── unit/
│   ├── domain/                  ← Testy encji, VO, serwisów domenowych — bez I/O, bez mocków portów
│   └── application/             ← Handlery z InMemory* adapterami i Fake* portami
│       ├── test_import_task.py
│       ├── test_workflow.py
│       ├── test_logging_publishers.py
│       └── test_outbox.py
├── integration/
│   ├── sql_sqlite/
│   │   └── __init__.py          ← Testy repozytoriów i UoW przez prawdziwe SQLite (aiosqlite)
│   ├── sql_postgres/
│   │   └── __init__.py          ← Jak wyżej, ale Postgres — pomijane gdy brak PG_TEST_URL
│   └── filesystem/              ← Operacje FS z tmp_path
├── e2e/
│   ├── cli/
│   │   └── test_tasker_full_graph.py   ← Pełne cykle orkiestracji przez CLI
│   └── api/
│       └── test_api.py          ← FastAPI TestClient: HTTP → CommandBus → DB
```

**Wzorzec unit testu handlera** (korzysta z InMemory adapterów):

```python
async def test_import_task_saves_to_repo() -> None:
    from shell.application.command_handlers.import_task_handler import ImportTaskHandler
    from shell.application.commands.commands import ImportTaskCommand
    from shell.infrastructure.persistence.memory.memory import (
        InMemoryUnitOfWork, FakeClock, FakeIdGenerator, FakeEventPublisher, FakeTaskLoader,
    )

    uow = InMemoryUnitOfWork()
    handler = ImportTaskHandler(
        uow=uow,
        clock=FakeClock(),
        id_gen=FakeIdGenerator(),
        task_loader=FakeTaskLoader(body="# Test"),
        events=FakeEventPublisher(),
    )
    task_id = await handler.handle(ImportTaskCommand(md_path="t.md", yaml_path="t.yaml", task_name="t"))
    assert task_id is not None
```

---

## 7. Architektura warstwowa

```
domain ← application ← infrastructure ← framework ← bootstrap
```

Importy idą **tylko w tym kierunku** — żadna niższa warstwa nie może importować z wyższej.

| Warstwa | Co zawiera | Dozwolone importy |
|---|---|---|
| `domain/` | Encje, VO, porty repozytoriów, eventy domenowe, wyjątki | Tylko stdlib |
| `application/` | Komendy, zapytania, handlery, porty (Protocol), strategie | `domain/` + stdlib |
| `infrastructure/` | Adaptery SQL/Memory/FS/Process, logging, messaging | `domain/` + `application/` + libs |
| `framework/` | CLI (argparse) + FastAPI | `domain/` + `application/` + `infrastructure/` |
| `bootstrap/` | `ApplicationFactory` — składa wszystko razem | Wszystkie warstwy |
| `shared/` | `UuidIdGenerator` i inne pomocnicze | Tylko stdlib |

---

## 8. Mapa plików — co gdzie jest

### domain/

```
domain/
├── entities/
│   ├── task.py              Task, Graph, Node
│   ├── workflow.py          Workflow, NodeState
│   ├── envelope.py          Envelope, EnvelopeEvent
│   ├── node_result.py       NodeResult
│   ├── prompt.py            Prompt
│   ├── runner_config.py     RunnerConfig
│   ├── rag_document.py      RagDocument, RagChunk
│   └── session.py           Session, Message
├── value_objects/
│   ├── ids.py               TaskId, WorkflowId, EnvelopeId, NodeId, ...
│   ├── task_name.py         TaskName
│   ├── status.py            Status (pending/running/done/failed)
│   ├── envelope_status.py   EnvelopeStatus
│   └── ...
├── repositories/            Porty (Protocol) — czyste interfejsy bez implementacji
│   ├── task_repository.py
│   ├── workflow_repository.py
│   └── ...
├── events/
│   └── events.py            TaskImported, WorkflowStarted, EnvelopeRouted, NodeCompleted, ...
├── services/
│   ├── graph_routing_service.py
│   └── rag_index_service.py
└── exceptions.py            DomainError i podklasy
```

### application/

```
application/
├── commands/
│   └── commands.py          Wszystkie Command dataclassy (frozen=True)
├── queries/
│   └── queries.py           Wszystkie Query dataclassy (frozen=True)
├── command_handlers/        Jeden handler per plik
│   ├── import_task_handler.py
│   ├── start_workflow_handler.py
│   ├── route_envelopes_handler.py
│   ├── run_node_handler.py
│   ├── run_tasker_workflow_handler.py
│   ├── save_node_result_handler.py
│   ├── save_prompt_handler.py
│   ├── archive_envelope_handler.py
│   └── bootstrap_runner_config_handler.py
├── query_handlers/
│   └── query_handlers.py    GetWorkflowHandler, GetTaskByNameHandler, ...
├── dto/                     DTO zwracane przez handlery zapytań
├── mappers/                 Entity ↔ DTO
├── ports/
│   └── ports.py             UnitOfWork, Clock, IdGenerator, EventPublisher, Logger, NodeExecutionProcessRunner, TaskLoader
├── strategies/
│   ├── node_execution_strategy.py   (Protocol)
│   ├── agent_strategy.py
│   ├── router_strategy.py
│   ├── tasker_strategy.py
│   ├── tool_strategy.py
│   └── worker_strategy.py
└── bus.py                   CommandBus, QueryBus, EventBus
```

### infrastructure/

```
infrastructure/
├── persistence/
│   ├── sql/
│   │   ├── __init__.py           build_session_factory(), create_all_tables()
│   │   ├── models/               SQLAlchemy ORM modele (TaskModel, WorkflowModel, ...)
│   │   ├── repositories/         SqlTaskExecutionRepository, SqlWorkflowRepository, ...
│   │   └── unit_of_work.py       SqlAlchemyUnitOfWork
│   ├── memory/
│   │   └── memory.py             InMemoryUnitOfWork, FakeClock, FakeIdGenerator, FakeEventPublisher, FakeTaskLoader
│   └── migrations/
│       └── sql/versions/
│           ├── 001_initial.py
│           ├── 002_rag_session.py
│           ├── 003_audit_event.py
│           └── 004_outbox.py
├── filesystem/
│   ├── task_loader.py            Czyta .md + .yaml z dysku → TaskBody
│   ├── node_workspace.py         Zarządza katalogiem roboczym node'a
│   └── envelope_archive_fs.py    FS-based archiwum kopert
├── process/
│   └── subprocess_runner.py      NodeExecutionProcessRunner — uruchamia node'y przez subprocess
├── logging/
│   ├── stdlib_logger.py          StdlibLogger (JSON output, correlation_id)
│   ├── logging_event_publisher.py
│   ├── sql_audit_publisher.py    Zapis do tabeli audit_event
│   └── composite_event_publisher.py
├── messaging/
│   ├── sql_outbox_publisher.py   Zapis do tabeli outbox_event
│   ├── memory_outbox_store.py    InMemory outbox (testy)
│   └── outbox_to_inbox_relay.py           Relay: czyta outbox → wysyla do inbox
├── rag/                          RAG repozytoria
└── configuration/                Settings (pydantic-settings)
```

### framework/

```
framework/
├── cli/
│   ├── main.py       Dispatcher: argv → subkomenda → asyncio.run(handler)
│   └── parser.py     build_parser() — wspólny argparse dla wszystkich trybów
└── api/
    ├── app.py                create_app(container) → FastAPI
    ├── routers/
    │   ├── tasks.py          POST /tasks/import, GET /tasks/{name}
    │   ├── workflows.py      POST /workflows, GET /workflows/{id}, POST /{id}/route
    │   ├── envelopes.py      GET /workflows/{id}/envelopes
    │   └── nodes.py          GET /nodes/{id}/result
    └── middleware/
        ├── correlation_id.py CorrelationIdMiddleware (X-Correlation-Id header)
        └── error_handler.py  DomainError → HTTP 4xx
```

### bootstrap/

```
bootstrap/
├── container.py   ApplicationFactory.build() → Container(command_bus, query_bus, event_bus)
└── main.py        python -m shell.bootstrap.main smoke|relay
```

---

## 9. Agregaty i ich relacje

```mermaid
graph TD
    Task -->|ma| Graph
    Graph -->|zawiera| Node
    Workflow -->|śledzi| NodeState
    Workflow -->|powiązany z| Task
    Envelope -->|należy do| Workflow
    Envelope -->|dotyczy| Node
    NodeResult -->|wynik| Envelope
    Prompt -->|używany przez| Node
    RunnerConfig -->|konfiguruje| Node
    RagDocument -->|zawiera| RagChunk
    Session -->|zawiera| Message
```

---

## 10. Szyny

### Rejestracja handlera

Wszystkie handlery są rejestrowane w `bootstrap/container.py`:

```python
command_bus.register(ImportTaskCommand, import_task_handler)
query_bus.register(GetWorkflowQuery, get_workflow_handler)
event_bus.subscribe(TaskImported, on_task_imported)
```

### Wywołanie z kodu

```python
# Command (zapis stanu)
task_id: TaskId = await container.command_bus.dispatch(
    ImportTaskCommand(md_path="...", yaml_path="...", task_name="...")
)

# Query (odczyt bez efektów ubocznych)
dto: WorkflowDto | None = await container.query_bus.dispatch(
    GetWorkflowQuery(workflow_id="<uuid>")
)
```

---

## 11. Persistence — adaptery bazodanowe

### Tabele SQL

| Tabela | Zawiera |
|---|---|
| `task` | Zadania (md_body, yaml_body, graph JSON) |
| `workflow` | Instancje workflow + status |
| `node_state` | Stan każdego node'a w workflow |
| `envelope` | Koperty routingu |
| `node_result` | Wyniki wykonania node'ów |
| `prompt` | Przechowywane prompty |
| `runner_config` | Konfiguracje runnerów |
| `rag_document` | Dokumenty RAG |
| `rag_chunk` | Chunki dokumentów RAG |
| `session` | Sesje konwersacji |
| `message` | Wiadomości w sesjach |
| `audit_event` | Logi eventów domenowych (append-only) |
| `outbox_event` | Transactional outbox (at-least-once delivery) |

### Migracje

Migracje są aplikowane automatycznie przy każdym `ApplicationFactory.build()` przez `create_all_tables()`.  
Pliki migracji: `infrastructure/persistence/migrations/sql/versions/`.

### Zmiana backendu

```powershell
# SQLite (domyślny, bez konfiguracji)
$env:shell_DATABASE_URL = "sqlite+aiosqlite:///shell.db"

# PostgreSQL
$env:shell_DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/shell_db"
```

---

## 12. Observability

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

`SqlOutboxPublisher` zapisuje eventy do `outbox_event` z `published_at = NULL`.  
`OutboxRelay.run_once()` pobiera niepublikowane wpisy i przekazuje je downstream, ustawiając `published_at`.

```powershell
# Uruchom relay ręcznie
python -m shell.bootstrap.main relay --db-url sqlite+aiosqlite:///shell.db
```
