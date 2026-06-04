# Plan: Migracja SHELL → shell_ddd (DDD + Hexagonal + CQRS)

Migracja 1:1 funkcjonalności obecnego SHELL do nowego katalogu `./shell_ddd/` w tym samym repo. Jeden bounded context `shell`, klasyczne warstwy DDD, standardowy styl pythonowy (dataclasses, typing.Protocol, brak slotów/`x_` properties/`internal/_init_*.py`). Dwa wejścia: CLI (per-mode, jak dziś) + FastAPI (control plane). Persistence: port + adaptery SQLite (pełny), PostgreSQL (pełny), MongoDB (stub document-shape). Plan jest fazowany — każda faza ma weryfikację.

---

## Ocena dopasowania DDD/Hex/CQRS do SHELL

**Werdykt: dopasowanie częściowe, da się sensownie zrobić — ale z zastrzeżeniami.**

**Co naturalnie pasuje:**
- Są wyraźne agregaty: `Task` (+ `Graph`, `GraphNode`), `Workflow` (+ `Envelope`, `NodeState`), `Node`/`SubNode`, `Prompt`, `NodeResult`, `RunnerConfig`. Każdy ma tożsamość i cykl życia w DB.
- Istnieją już porty (`SqlDriver` → `SqliteDriver`/`PostgresDriver`, `MemoryBackend`) — Hex jest naturalną ewolucją.
- Operacje są dobrze odseparowane (`task_repo.import_task_files`, `router.run`, `archive`, `route_envelope`) — to gotowe Command/Query.
- Wymienialne DB (SQLite/Postgres/Mongo) to klasyczna sytuacja, gdzie Hex zwraca z odsetkami.

**Co zgrzyta:**
1. **Mongo + agregaty DB-first** — obecny schemat (workflow/envelope/event/archive) jest mocno relacyjny (FK, normalizacja). Wymienialność na Mongo wymaga albo (a) document-shaped agregatów (zmiana modelowania) albo (b) Mongo będzie wieczne „TODO”. Rekomendacja: **port `+` SQLite teraz, Postgres jako 2. adapter, Mongo jako stub** — ale dorzucę go w planie skoro tak wybrałeś.
2. **CLI vs FastAPI** — SHELL to runtime jednego node'a; FastAPI ma sens jako *control plane* (start workflow, query envelopes, query results) ale **nie zastąpi entrypointów per-node** odpalanych przez subprocess. Plan zakłada FastAPI jako drugie wejście do tych samych Command/Query handlers (control plane), CLI per-mode zostaje jako tryb wykonania jednego node'a.
3. **Subprocess execution** — uruchamianie node'ów przez subprocess to wewnętrzna integracja, w czystym DDD ląduje w `Infrastructure/ExternalServices` jako `NodeProcessRunner` (port w Application).
4. **Lazy/DOM wrappery (`AppNode`, `SubNode`, `Node` jako folder-DOM)** — to anty-wzorzec z punktu widzenia DDD. Zastępujemy je: agregaty (czyste dataclasses), `NodeWorkspace` jako Infrastructure service do operacji na FS.
5. **Mode dispatch (`agent/router/tasker/tool/worker`)** — pięć modułów to dziś bardziej *strategie wykonania* niż osobne BC. Skoro wybrałeś „jeden BC shell” — będą to **Strategy** w warstwie Application: `NodeExecutionStrategy` (port) + 5 implementacji (`AgentStrategy`, `RouterStrategy`, …).

**Ryzyka:**
- 1:1 migracja całej funkcjonalności jest duża (szacunkowo 80–120 plików w shell_ddd). Trzeba ją robić *fazami z weryfikacją*, nie big-bang.
- Czysty DDD + standardowy styl pythonowy = znacząca utrata Twoich obecnych konwencji (sloty/`x_`/`internal/_init_*.py`). Plan tego nie miesza — `shell_ddd` jest pisany od zera w stylu standardowym.

---

## Założenia globalne

- **Lokalizacja:** `c:\Users\palysiewicz\IdeaProjects\SHELL\shell_ddd\` (obok obecnego `shell/`).
- **Stary kod** (`shell/`, `agent/`, `router/`, `tasker/`, `tool/`, `worker/`) **NIE jest modyfikowany** — pełni rolę referencji i regresji.
- **Język/styl:** Python 3.11+, `dataclass(frozen=True)` dla VO i Commands/Queries, `dataclass` dla encji mutowalnych, `typing.Protocol` dla portów, `pydantic v2` dla DTO/Settings, `typing.Annotated` + `Depends` dla FastAPI.
- **DI:** prosty kontener typu `dependency-injector` LUB ręczna `ApplicationFactory` (rekomendacja: ręczna factory + Protocol, bez framework DI — mniej magii).
- **Brak konwencji obecnych:** żadnych `_slot` + `slot_` property, żadnych `internal/_init_*.py`. Funkcje pomocnicze są normalnymi funkcjami modułu lub metodami klasy.
- **Operacje plikowe:** używamy `pathlib.Path` + cienki helper `infrastructure/filesystem/` (nie portujemy `UtilsPath` 1:1).
- **Testy:** `pytest` + `pytest-asyncio`. Każda faza dorzuca testy: jednostkowe (domain/application bez DB) + integracyjne (per adapter).
- **Asynchroniczność:** Application + Infrastructure **async** (`async def handle`, `AsyncSession`, `httpx.AsyncClient`). CLI synchroniczne wejście wywołuje `asyncio.run(handler.handle(cmd))`.

---

## Architektura docelowa

```
shell_ddd/
├── domain/
│   ├── entities/             # Task, Workflow, Node, Envelope, NodeResult, Prompt, RunnerConfig
│   ├── value_objects/        # TaskName, NodeId, WorkflowId, EnvelopeId, Hash, Mode, Role, NodeMode, EnvelopeStatus, EnvelopeStage
│   ├── repositories/         # PORTS: TaskRepository, WorkflowRepository, EnvelopeRepository, PromptRepository, NodeResultRepository, RunnerConfigRepository, EnvelopeArchive
│   ├── services/             # GraphRoutingService, EnvelopeLifecycleService (czyste reguły domenowe)
│   ├── events/               # TaskImported, WorkflowStarted, EnvelopeRouted, EnvelopeExpired, NodeCompleted, NodeFailed
│   └── exceptions.py
├── application/
│   ├── commands/             # ImportTaskCommand, StartWorkflowCommand, RunNodeCommand, RouteEnvelopesCommand, ArchiveEnvelopeCommand, SaveNodeResultCommand, SavePromptCommand, BootstrapRunnerConfigCommand
│   ├── command_handlers/
│   ├── queries/              # GetTaskByName, GetCurrentTask, GetGraphNodes, GetWorkflow, GetEnvelopesByWorkflow, GetNodeResult, GetPrompt
│   ├── query_handlers/
│   ├── dto/                  # TaskDto, WorkflowDto, EnvelopeDto, NodeResultDto, PromptDto
│   ├── mappers/              # entity ↔ DTO (domain stays clean)
│   ├── ports/                # APPLICATION-LEVEL PORTS: UnitOfWork, NodeProcessRunner, NodeWorkspace, Clock, IdGenerator, EventPublisher, Logger
│   ├── strategies/           # NodeExecutionStrategy (port) + AgentStrategy, RouterStrategy, TaskerStrategy, ToolStrategy, WorkerStrategy
│   ├── event_handlers/       # subscribers dla domain events (np. AutoArchiveOnNodeCompleted)
│   └── bus.py                # CommandBus, QueryBus, EventBus (in-memory)
├── infrastructure/
│   ├── persistence/
│   │   ├── sql/
│   │   │   ├── session_factory.py   # AsyncSession factory (sqlite+aiosqlite, postgres+asyncpg)
│   │   │   ├── models/              # SQLAlchemy 2.x ORM models (osobne od domain)
│   │   │   ├── mappers/             # SQL model ↔ domain entity
│   │   │   ├── repositories/        # SqlTaskRepository, SqlWorkflowRepository, SqlEnvelopeRepository, ...
│   │   │   └── unit_of_work.py      # SqlAlchemyUnitOfWork (Postgres + SQLite współdzielą)
│   │   ├── mongo/
│   │   │   ├── client.py            # motor AsyncIOMotorClient
│   │   │   ├── documents/           # Pydantic document models (document-shape per aggregate)
│   │   │   ├── mappers/
│   │   │   ├── repositories/        # MongoTaskRepository, MongoWorkflowRepository, ...
│   │   │   └── unit_of_work.py      # MongoUnitOfWork (transakcje na replica set lub no-op fallback)
│   │   ├── memory/                  # InMemory* implementacje wszystkich repo (do testów i lokalnego dev)
│   │   └── migrations/              # alembic dla SQL, jeden katalog versions/ per adapter
│   ├── filesystem/
│   │   ├── node_workspace.py        # zamiennik AppNode/Node folder DOM; tworzy/sprząta katalogi node'a
│   │   ├── task_loader.py           # czyta task.md + task.yaml z dysku
│   │   └── envelope_archive_fs.py   # filesystem-based EnvelopeArchive adapter
│   ├── process/
│   │   ├── subprocess_runner.py     # NodeProcessRunner adapter (subprocess.run / asyncio.create_subprocess_exec)
│   │   └── command_builder.py       # buduje argv dla agent/router/tasker/tool/worker
│   ├── messaging/
│   │   ├── inmemory_event_bus.py
│   │   └── outbox/                  # transactional outbox (opcjonalne, faza późniejsza)
│   ├── external/                    # placeholdery: CopilotGateway, LlmGateway
│   ├── configuration/
│   │   ├── settings.py              # pydantic-settings: DATABASE_KIND, DATABASE_URL, MONGO_URL, ...
│   │   ├── manifest_loader.py       # ładuje manifest.yaml
│   │   └── config_loader.py         # ładuje config.yaml + składa Config
│   ├── logging/
│   │   └── stdlib_logger.py
│   └── time/
│       └── system_clock.py
├── framework/
│   ├── cli/
│   │   ├── main.py                  # entry: python -m shell_ddd.framework.cli ...
│   │   ├── commands/                # typer/argparse subcommands per mode
│   │   │   ├── agent.py
│   │   │   ├── router.py
│   │   │   ├── tasker.py
│   │   │   ├── tool.py
│   │   │   └── worker.py
│   │   └── dispatcher.py            # mapuje argparse → Command → CommandBus
│   ├── api/
│   │   ├── app.py                   # FastAPI factory
│   │   ├── routers/
│   │   │   ├── tasks.py             # POST /tasks/import, GET /tasks/{name}
│   │   │   ├── workflows.py         # POST /workflows, GET /workflows/{id}
│   │   │   ├── envelopes.py         # GET /workflows/{id}/envelopes
│   │   │   └── nodes.py             # GET /nodes/{id}/result
│   │   ├── request_models.py        # pydantic Request
│   │   ├── response_models.py
│   │   └── middleware/
│   │       ├── correlation_id.py
│   │       └── error_handler.py
│   └── entrypoints/                 # cienkie shimy zastępujące dawne entrypoint.py modułów
│       ├── agent_entrypoint.py
│       ├── router_entrypoint.py
│       ├── tasker_entrypoint.py
│       ├── tool_entrypoint.py
│       └── worker_entrypoint.py
├── bootstrap/
│   ├── settings.py                  # re-export, layered (env + .env + defaults)
│   ├── container.py                 # ApplicationFactory: builds CommandBus/QueryBus z handlerami + DI
│   ├── application_factory.py
│   └── main.py                      # __main__ — wybiera CLI lub uvicorn na podstawie ENV/arg
├── shared/
│   ├── result.py                    # Result[T, E] pattern (opcjonalnie)
│   ├── ids.py                       # UUID generatory
│   └── types.py                     # type aliases
├── tests/
│   ├── unit/
│   │   ├── domain/
│   │   └── application/
│   ├── integration/
│   │   ├── sql_sqlite/
│   │   ├── sql_postgres/            # wymaga docker-compose
│   │   └── mongo/                   # wymaga docker-compose
│   ├── e2e/
│   │   ├── cli/
│   │   └── api/
│   └── conftest.py
├── docker-compose.test.yml          # postgres + mongo dla integracyjnych
├── pyproject.toml                   # osobny od głównego (lub aktualizacja głównego o dependency-group `shell_ddd`)
└── README.md
```

**Reguła zależności:** `domain ← application ← infrastructure ← framework ← bootstrap`. Imports nigdy w drugą stronę. Domain nie importuje niczego poza stdlib.

---

## Mapowanie obecne → docelowe

| Obecne | Docelowe (warstwa / nazwa) |
|---|---|
| `shell/task/task_record.py` (`TaskRecord`) | `domain/entities/task.py` (`Task`) + `domain/value_objects/task_name.py` (`TaskName`) |
| `shell/task/graph_node_record.py` | `domain/entities/graph_node.py` (`GraphNode`) — agregat `Task` zawiera `Graph` zawierający `list[GraphNode]` |
| `shell/task/task_repo/task_repo.py` | port `domain/repositories/task_repository.py` + adaptery `infrastructure/persistence/{sql,mongo,memory}/repositories/*_task_repository.py` |
| `shell/task/task_schema/internal/_apply_task_schema.py` | `infrastructure/persistence/sql/migrations/versions/0001_task.py` (alembic) |
| `shell/bus/envelope/envelope.py` (+ stage/status enums) | `domain/entities/envelope.py` + `domain/value_objects/envelope_status.py`, `envelope_stage.py` |
| `shell/bus/workflow_state/workflow_state.py` | `domain/entities/workflow.py` (agregat `Workflow` z `list[Envelope]` + `node_states`) |
| `shell/bus/message_bus/message_bus.py` | `application/commands/RouteEnvelopesCommand` + handler; persystencja: `EnvelopeRepository` |
| `shell/bus/envelope_archiver/` | port `domain/repositories/envelope_archive.py` + adapter `infrastructure/filesystem/envelope_archive_fs.py` (+ adapter SQL `envelope_archive_sql.py` opcjonalnie) |
| `shell/component/prompt_repo/` | port + `Sql/Mongo/MemoryPromptRepository`; encja `domain/entities/prompt.py` |
| `shell/component/node_result_repo/` | port + adaptery; encja `NodeResult` |
| `shell/component/runner_config_repo/` | port + adaptery; encja `RunnerConfig` |
| `shell/component/manifest/manifest.py` | VO `domain/value_objects/manifest.py` + loader w `infrastructure/configuration/manifest_loader.py` |
| `shell/component/config/` + `shell/component/placeholders/` | `infrastructure/configuration/config_loader.py` + `application/dto/runtime_config.py`. Placeholders → `infrastructure/configuration/placeholder_resolver.py` |
| `shell/component/cli/` | `framework/cli/commands/*` (argparse/typer) |
| `shell/component/process/` | `infrastructure/process/subprocess_runner.py` + `command_builder.py`. Port: `application/ports/node_process_runner.py` |
| `shell/component/prompt/`, `prompt_file/` | `domain/value_objects/prompt_file.py` + `infrastructure/filesystem/prompt_loader.py` |
| `shell/component/result/` | VO `domain/value_objects/execution_result.py` (stdout/stderr/returncode) |
| `shell/component/runtime/` | `infrastructure/configuration/runtime.py` (manifest + runtime_config + system info) |
| `shell/app/app/` (`App`) | **usuwamy**. Rolę pełni `bootstrap/application_factory.py` + handlery |
| `shell/app/app_node/`, `shell/structure/node/`, `shell/structure/sub_node/` | `infrastructure/filesystem/node_workspace.py` (FS operacje) + `domain/entities/node.py` (czysty model bez folder-DOM) |
| `shell/app/app_runner/` | `application/strategies/node_execution_strategy.py` + 5 implementacji w `application/strategies/{agent,router,tasker,tool,worker}_strategy.py` |
| `shell/app/app_trace/` | `application/ports/event_publisher.py` + `infrastructure/logging/` + tabela `audit_event` przez `AuditRepository` |
| `shell/memory/sql_driver/` | `infrastructure/persistence/sql/session_factory.py` (SQLAlchemy 2.x async) |
| `shell/memory/memory_backend/` | usuwamy abstrakcję — zastępuje ją `UnitOfWork` + repo |
| `shell/memory/rag_index/` | `infrastructure/persistence/sql/rag/` lub osobny adapter (faza końcowa) |
| `shell/context/*` | Większość to plumbing — odbudowujemy minimum: `SessionContext` jako VO przekazywany przez handlery, `AuditContext` zastąpiony przez `EventPublisher` |
| `shell/logger/` | `infrastructure/logging/stdlib_logger.py` + port `application/ports/logger.py` |
| `shell/utils/*` | `infrastructure/filesystem/` (Path) + `shared/` (system, io) — bez całej `UtilsPath` klasy |
| `shell/status/` | VO `domain/value_objects/status.py` |
| `shell/module/{agent,router,tasker,tool,worker}/` | logika *strategii* idzie do `application/strategies/`; ich osobne `*_prompt`, `*_properties` lądują jako: prompty → `domain/value_objects` + `infrastructure/filesystem/prompt_loader.py`, properties → pola Command/Query |
| `agent/cli-agent/entrypoint.py`, `router/default-router/entrypoint.py`, itd. | `framework/entrypoints/*_entrypoint.py` — każdy wywołuje `ApplicationFactory().cli().dispatch(['--mode', '...'])` |

**Tabele DB → agregaty:**
- Agregat **Task**: `task`, `graph`, `graph_node` (root: `Task`)
- Agregat **Workflow**: `workflow`, `node_state` (root: `Workflow`)
- Agregat **Envelope**: `envelope`, `envelope_event` (root: `Envelope`) — referencja do `workflow_id` (cross-aggregate by id)
- Agregat **EnvelopeArchive**: `envelope_archive` (root osobno bo write-only/append-only)
- Agregat **Prompt**: `prompt`
- Agregat **NodeResult**: `node_result`
- Agregat **RunnerConfig**: `runner_config`
- Agregat **Session/Message/Audit**: `session`, `message`, `audit_event`
- Agregat **RagDocument**: `rag_document`, `rag_chunk`

---

## Fazy migracji

Każda faza ma: cel, kroki, pliki, weryfikację. Fazy 0–3 to fundament. Fazy 4+ to migracja funkcjonalna (każda dorzuca jeden agregat E2E przez wszystkie warstwy i wszystkie 3 persistence). Fazy można częściowo zrównoleglać po fazie 3 (oznaczone *parallel*).

### **Faza 0 — Setup projektu** ✅ ZAKOŃCZONA (blokuje wszystko)

Cel: pusty, ale działający szkielet z testami, lintem, CI lokalnym.

1. Utwórz katalog `shell_ddd/` z drzewem powyżej (puste `__init__.py` w każdym pakiecie).
2. Utwórz `shell_ddd/pyproject.toml` z dependencjami: `fastapi`, `uvicorn[standard]`, `pydantic>=2`, `pydantic-settings`, `sqlalchemy>=2.0`, `aiosqlite`, `asyncpg`, `alembic`, `motor`, `typer` (lub stdlib argparse), `pyyaml`, `pytest`, `pytest-asyncio`, `httpx`, `mypy`, `ruff`.
3. Utwórz `docker-compose.test.yml` (postgres:16, mongo:7 z replSet rs0 dla transakcji).
4. Utwórz `shell_ddd/conftest.py` ze stubem fixture dla 3 backendów (skipif gdy brak dockera).
5. Utwórz `shell_ddd/README.md` z reguła zależności i komendami uruchomienia.
6. Pierwszy test: `tests/unit/domain/test_smoke.py` z `assert True`.

**Weryfikacja:** `pytest shell_ddd/tests -x` przechodzi. `ruff check shell_ddd` i `mypy shell_ddd` zwracają zero błędów.

### **Faza 1 — Domain core (bez persistence)** ✅ ZAKOŃCZONA

> Zaimplementowane: wszystkie VO, encje, porty repo, domain events, exceptions.
> Brakuje: `domain/services/` (GraphRoutingService, EnvelopeLifecycleService) — dodane w ramach uzupełnienia przed Faza 4.

Cel: wszystkie agregaty, VO, events, exceptions napisane jako czyste dataclasses + Protocol. Bez I/O.

1. **VO** (`domain/value_objects/`): `TaskName`, `Hash` (sha256 hex), `NodeId`, `WorkflowId`, `EnvelopeId`, `Mode` (Enum: agent/router/tasker/tool/worker), `Role` (str opaque), `NodeMode`, `EnvelopeStatus` (PENDING/ACTIVE/DELIVERED/FAILED/DEAD), `EnvelopeStage`, `Manifest` (name, mode, role, type, version), `ExecutionResult` (stdout, stderr, returncode), `Status` (frozen dataclass), `PromptFile` (file_name, file_body), `Timestamp`. Wszystkie `dataclass(frozen=True)` z walidacją w `__post_init__`.
2. **Entities** (`domain/entities/`): `Task` (id, name, version, hash, body_md, body_yaml_raw, is_current, created_at, graph: Graph), `Graph` (id, task_id, raw_dict, nodes: list[GraphNode]), `GraphNode` (id, position, node_dir, mode, role, type, model, command, timeout, retries, log_level, max_step, no_ask_user, autopilot, task_name, source_dir, work_dir, status_initial, extra: dict), `Workflow` (id, status, node_states: dict[NodeId, NodeState], created_at), `NodeState` (node_id, status, step, updated_at), `Envelope` (id, workflow_id, parent_id, correlation_id, sender_node_id, receiver_node_id, source_role, target_role, sequence_id, step, status, stage, payload, artifact_uri, archive_uri, created_at, updated_at, events: list[EnvelopeEvent]), `EnvelopeEvent`, `Prompt` (id, name, version, hash, body, source_uri, is_current, created_at), `NodeResult` (id, node_id, workflow_id, status, stdout, stderr, artifact_uri, created_at), `RunnerConfig` (id, package_name, kind, hash, body, created_at), `Node` (id, mode, role, type, workspace_path).
3. **Domain services** (`domain/services/`):
   - `GraphRoutingService.resolve_target_node(graph, source_node, target_role) -> NodeId` — przeniesienie logiki z `shell/module/router/router/internal/_run_router.py`.
   - `EnvelopeLifecycleService.advance(envelope, max_step) -> EnvelopeStatus` — TTL/expire logic.
4. **Repository PORTS** (`domain/repositories/`) jako `typing.Protocol` (async):
   - `TaskRepository` (save, find_current_by_name, find_by_id, list_by_name)
   - `WorkflowRepository` (save, find_by_id)
   - `EnvelopeRepository` (save, find_by_id, find_pending_by_workflow, find_active_by_workflow)
   - `EnvelopeArchive` (append, find_by_workflow)
   - `PromptRepository` (save, find_current_by_name)
   - `NodeResultRepository` (save, find_by_node_id, find_by_workflow)
   - `RunnerConfigRepository` (save, find_current_by_package_kind)
5. **Domain events** (`domain/events/`) frozen dataclasses: `TaskImported`, `WorkflowStarted`, `EnvelopeRouted`, `EnvelopeExpired`, `NodeCompleted`, `NodeFailed`, `PromptSaved`.
6. **Exceptions** (`domain/exceptions.py`): `DomainError` (base), `TaskNotFound`, `WorkflowNotFound`, `RoleNotResolvable`, `EnvelopeAlreadyDelivered`, `MaxStepExceeded`, `InvalidNodeMode`.

**Weryfikacja:** `tests/unit/domain/` — po jednym pliku per entity/VO/service, każdy testuje walidację i invariants. Pokrycie domain >=90% (`pytest --cov=shell_ddd/domain`). Zero importów z `application/`/`infrastructure/`/`framework/` w domenie (test custom: `tests/unit/domain/test_no_external_imports.py` skanujący `import` po AST).

### **Faza 2 — Application core** ✅ ZAKOŃCZONA

> Zaimplementowane: porty, Commands/Queries + handlery (Import, StartWorkflow, BootstrapRunnerConfig, SaveNodeResult, SavePrompt, query handlers), bus (CommandBus/QueryBus/EventBus), DTOs, mappers, InMemoryUoW + repozytoria.
> Uzupełnione w ramach domknięcia: RouteEnvelopesHandler, RunNodeHandler, ArchiveEnvelopeHandler, NodeExecutionStrategy (5 impl), event_handlers (ArchiveOnDelivered, LogAudit).

Cel: Commands/Queries + handlery + ports + bus. Bez infrastruktury — z `InMemory*` repo do testów.

1. **Application ports** (`application/ports/`):
   - `UnitOfWork` (Protocol: `__aenter__`, `__aexit__`, `commit`, `rollback`, properties dla każdego repo) — port; w infrastrukturze będzie `SqlAlchemyUoW`, `MongoUoW`, `InMemoryUoW`.
   - `NodeProcessRunner` (Protocol: `async run(command: NodeCommand) -> ExecutionResult`) — port subprocess.
   - `NodeWorkspace` (Protocol: `prepare(node)`, `archive(node, clock)`, `release(node)`, `read_input(node)`, `write_output(node, name, body)`) — port FS.
   - `Clock` (Protocol: `now() -> datetime`).
   - `IdGenerator` (Protocol: `new_workflow_id`, `new_envelope_id`, `new_node_result_id`, ...).
   - `EventPublisher` (Protocol: `async publish(events: list[DomainEvent])`).
   - `Logger` (Protocol).
2. **Commands + Handlers** (`application/commands/`, `application/command_handlers/`):
   - `ImportTaskCommand(name, md_path, yaml_path)` → `ImportTaskHandler` (loader → hash → repo.save w UoW → publish `TaskImported`).
   - `BootstrapRunnerConfigCommand(package_name, kind, body)` → handler.
   - `SavePromptCommand(name, body, source_uri)` → handler.
   - `StartWorkflowCommand(task_name, initial_payload, runner_root_dir)` → handler: loads task, creates Workflow, seeds first Envelope(PENDING).
   - `RouteEnvelopesCommand(workflow_id, max_step)` → handler: iteruje envelopes PENDING, używa `GraphRoutingService`, `EnvelopeLifecycleService`, zapisuje przez UoW, publikuje `EnvelopeRouted`/`EnvelopeExpired`.
   - `RunNodeCommand(workflow_id, node_id, mode, envelope_id)` → handler: wybiera `NodeExecutionStrategy` po `mode`, woła `strategy.execute`, zapisuje `NodeResult`, publikuje `NodeCompleted`/`NodeFailed`.
   - `ArchiveEnvelopeCommand(envelope_id)` → handler: marks DELIVERED, appends archive.
   - `SaveNodeResultCommand(...)` → handler.
3. **Queries + Handlers**:
   - `GetCurrentTaskQuery(name)` → `TaskDto`.
   - `GetGraphNodesQuery(task_id)` → `list[GraphNodeDto]`.
   - `GetWorkflowQuery(id)` → `WorkflowDto`.
   - `ListEnvelopesByWorkflowQuery(workflow_id, status?)` → `list[EnvelopeDto]`.
   - `GetNodeResultQuery(node_id)` → `NodeResultDto`.
   - `GetCurrentPromptQuery(name)` → `PromptDto`.
4. **Strategies** (`application/strategies/`):
   - `NodeExecutionStrategy` Protocol: `async execute(node: GraphNode, workspace: NodeWorkspace, runner: NodeProcessRunner, context: ExecutionContext) -> ExecutionResult`.
   - 5 impl: `AgentStrategy`, `RouterStrategy`, `TaskerStrategy`, `ToolStrategy`, `WorkerStrategy`. Każda buduje `NodeCommand` (argv) z `command_builder` portem i wywołuje runner. Mapowanie obecne: agent uses prompt+model+timeout (z `shell/module/agent/agent/internal/_run_agent.py`), router uses graph routing (przeniesione już do `GraphRoutingService`), tasker spawnuje sub_node'y (rekurencja przez `CommandBus.dispatch(RunNodeCommand)`).
5. **Bus** (`application/bus.py`): `CommandBus` (`register(cmd_type, handler)`, `async dispatch(cmd)`), `QueryBus`, `EventBus` (in-memory pub/sub). Handlery dostają zależności przez `__init__` (constructor injection).
6. **Event handlers** (`application/event_handlers/`):
   - `ArchiveOnDeliveredHandler` (subskrybuje `EnvelopeRouted` z stage=DELIVERED).
   - `LogAuditHandler` (loguje wszystkie eventy do audit).
7. **InMemoryUoW + repo** (`infrastructure/persistence/memory/`): pełne implementacje dla wszystkich portów (do testów).

**Weryfikacja:**
- `tests/unit/application/` — handler per file, używa `InMemoryUoW` + `FakeClock` + `FakeIdGenerator`. Każdy testuje: happy path, brak rekordu, walidacja.
- `tests/unit/application/test_strategies.py` — strategie testowane z `FakeNodeProcessRunner` zwracającym scenariusze (ok/timeout/error).
- Test architektoniczny: `tests/unit/test_layer_dependencies.py` — AST scanner: `application/` nie importuje `infrastructure/` ani `framework/`.

### **Faza 3 — Infrastructure: SQLite (pierwszy pełny adapter)** ✅ ZAKOŃCZONA

> Zaimplementowane: session_factory, modele ORM, mappery SQL, repozytoria SQL, SqlAlchemyUnitOfWork, testy integracyjne SQLite.
> Uzupełnione: bootstrap/ApplicationFactory, alembic migrations stub, testy przeniesione do test_*.py.

Cel: wszystkie repo + UoW działają na SQLite (aiosqlite). Migracje alembic.

1. `infrastructure/persistence/sql/session_factory.py` — `create_async_engine`, `async_sessionmaker(expire_on_commit=False)`. Konfig z `Settings.database_url`.
2. `infrastructure/persistence/sql/models/` — ORM models 1:1 ze schematem obecnym (`task`, `graph`, `graph_node`, `workflow`, `node_state`, `envelope`, `envelope_event`, `envelope_archive`, `prompt`, `node_result`, `runner_config`, `audit_event`, `session`, `message`). FK + indeksy zachowane.
3. `infrastructure/persistence/sql/mappers/` — funkcje `to_domain(model) -> Entity` i `to_model(entity) -> Model`. Czyste; bez side effects.
4. `infrastructure/persistence/sql/repositories/` — każdy implementuje Port; dostaje `AsyncSession` przez `__init__`.
5. `infrastructure/persistence/sql/unit_of_work.py` — `SqlAlchemyUnitOfWork`:
   ```
   async __aenter__: session = factory(); seed repo properties
   async __aexit__: rollback if exc else nothing
   async commit: await session.commit()
   ```
6. `infrastructure/persistence/migrations/sql/` — alembic init; pierwsza migracja `0001_initial.py` z całością schematu (tabele identyczne z `_apply_task_schema` + `bus_schema` + reszta).
7. `bootstrap/container.py` — `ApplicationFactory.build(settings) -> Container` rejestrujący handlery, podstawiający `SqlAlchemyUoW` jako `UnitOfWork`.

**Weryfikacja:**
- `tests/integration/sql_sqlite/` — uruchamia każdy handler na realnym SQLite (`:memory:` lub tymczasowy plik), sprawdza zapis/odczyt + commit/rollback.
- Suite: `test_import_task`, `test_start_workflow`, `test_route_envelopes`, `test_archive_envelope`, `test_save_node_result`, `test_save_prompt` + Query odpowiedniki.
- Komenda: `pytest shell_ddd/tests/integration/sql_sqlite -x`.

### **Faza 4 — Infrastructure: subprocess + filesystem** ✅ ZAKOŃCZONA

Cel: realne uruchamianie node'ów + operacje FS.

1. `infrastructure/process/subprocess_runner.py` — `SubprocessNodeProcessRunner` (asyncio `create_subprocess_exec`, capture stdout/stderr, timeout via `asyncio.wait_for`).
2. `infrastructure/process/command_builder.py` — buduje argv per mode (port `application/ports/command_builder.py`). Przeniesione z `shell/component/process/process_command/internal/*`.
3. `infrastructure/filesystem/node_workspace.py` — tworzy strukturę `.node/{input,output,logs,temp,prompt,scripts,status,port,archive}`. Operacje: prepare/release/archive/read_input/write_output.
4. `infrastructure/filesystem/task_loader.py` — read `.md` + `.yaml`, hash content.
5. `infrastructure/filesystem/prompt_loader.py` — ładuje `*.prompt.md`.
6. `infrastructure/filesystem/envelope_archive_fs.py` — implementacja `EnvelopeArchive` portu na FS (alternatywa dla wersji SQL).

**Weryfikacja:** `tests/integration/process/` z tymczasowym katalogiem (`tmp_path`) — uruchamia echo/cat, weryfikuje stdout/timeout/returncode. `tests/integration/filesystem/` — workspace lifecycle.

### **Faza 5 — Framework: CLI** ✅ ZAKOŃCZONA

Cel: pełne CLI per mode, behaviorally compatible z obecnym (te same flagi).

1. `framework/cli/main.py` — `Typer()` (lub argparse) z subcommands: `agent`, `router`, `tasker`, `tool`, `worker`, `import-task`, `route`, `workflow start`, `workflow status`.
2. Per subcommand: `framework/cli/commands/agent.py` itd. — parsuje flagi (`--source-dir`, `--node-dir`, `--runner-root-dir`, `--prompt`, `--model`, …), buduje `RunNodeCommand`/`StartWorkflowCommand`, woła `await container.command_bus.dispatch(...)`.
3. `framework/entrypoints/{agent,router,tasker,tool,worker}_entrypoint.py` — cienkie shimy zachowujące zgodność z obecnymi `agent/cli-agent/entrypoint.py` itd. (te same argv, te same exit codes). Każdy: `if __name__ == '__main__': asyncio.run(framework.cli.main.app(['agent', *sys.argv[1:]]))`.
4. `bootstrap/main.py` — wybór CLI vs API przez argv[0]/env.

**Weryfikacja:** `tests/e2e/cli/` — odpala subprocess CLI z prawdziwym SQLite plikiem, asercja exit code + zawartość DB. Jeden test per mode.

### **Faza 6 — Framework: FastAPI (control plane)** ✅ ZAKOŃCZONA

Cel: control plane endpoints.

1. `framework/api/app.py` — `create_app(container) -> FastAPI` z lifespan zarządzającym `engine.dispose()`.
2. Routers:
   - `tasks.py`: `POST /tasks/import` (multipart md+yaml lub paths), `GET /tasks/{name}`, `GET /tasks/{name}/graph`.
   - `workflows.py`: `POST /workflows` (start), `GET /workflows/{id}`, `POST /workflows/{id}/route` (manual route trigger).
   - `envelopes.py`: `GET /workflows/{id}/envelopes`, `GET /envelopes/{id}`.
   - `nodes.py`: `GET /nodes/{id}/result`.
3. DI w endpointach: `container = Depends(get_container)` → `bus = container.command_bus`.
4. Middleware: correlation_id (per request UUID w log context), error_handler (DomainError → 400/404, inne → 500).
5. `bootstrap/main.py` rozszerzone: `python -m shell_ddd serve` → uvicorn.

**Weryfikacja:** `tests/e2e/api/` z `httpx.AsyncClient(app=app)`. Pełen happy path: import task → start workflow → list envelopes → get result.

### **Faza 7 — Infrastructure: PostgreSQL** ✅ ZAKOŃCZONA *(parallel z fazą 8 po fazie 6)*

Cel: drugi adapter SQL — Postgres przez asyncpg.

1. Rozszerz `session_factory.py` o sterownik `postgresql+asyncpg`.
2. Drugi katalog `migrations/sql_postgres/versions/` — alembic env z innym dialektem (lub jeden env z auto-detect).
3. Adaptery repo — w 95% wspólne (SQLAlchemy 2.x); różnice tylko w typach kolumn (JSONB vs JSON, GIN indexes opcjonalnie).
4. `docker-compose.test.yml` → service `postgres`. `conftest.py` fixture `postgres_engine` (skipif brak `PG_TEST_URL`).
5. Settings: `DATABASE_KIND=postgres|sqlite|mongo` przełącza adaptery w `ApplicationFactory`.

**Weryfikacja:** `pytest shell_ddd/tests/integration/sql_postgres -x` — uruchamiany w docker-compose.

### **Faza 8 — Infrastructure: MongoDB** ⏸ WSTRZYMANA *(do pominięcia — Mongo odkładamy na później)*

Cel: trzeci adapter — Mongo (motor). Document-shape per agregat (kompromis vs relacyjne).

1. `infrastructure/persistence/mongo/client.py` — `AsyncIOMotorClient(MONGO_URL)`.
2. `documents/` — pydantic models reprezentujące dokumenty:
   - `task_document` (top-level: task fields + embedded `graph.nodes[]`).
   - `workflow_document` (top-level workflow + embedded `node_states[]`).
   - `envelope_document` (top-level envelope + embedded `events[]`; `workflow_id` jako referencja).
   - itd.
3. `mappers/` — entity ↔ document.
4. `repositories/` — implementują porty (find/save). Złożone query (np. `find_pending_by_workflow`) używają Mongo filtrami.
5. `unit_of_work.py` — `MongoUnitOfWork` z `async with client.start_session() as session: session.start_transaction()`. Wymaga replica set (compose: `mongo --replSet rs0`). Fallback: `NoTxMongoUnitOfWork` (best-effort, log warning).
6. `migrations/mongo/` — skrypty Python tworzące collections + indeksy (`db.envelope.create_index([('workflow_id', 1)])` itp.).

**Weryfikacja:** `pytest shell_ddd/tests/integration/mongo -x`.

### **Faza 9 — Memory / RAG / Context** ✅ ZAKOŃCZONA

Cel: przenieś `shell/memory/rag_index/`, `shell/context/*` jako dodatkowe agregaty/serwisy.

1. `domain/entities/`: `RagDocument`, `RagChunk`, `ContextEntry`, `Session`, `Message`.
2. Repos + adaptery dla wszystkich 3 backendów (Mongo dla RAG opcjonalnie z `$vectorSearch`).
3. Port `Embedder` (Protocol) + adapter `HashEmbedder` (przeniesiony z `shell/memory/rag_index/embedder/`).
4. Commands: `IndexDocumentCommand`, `SearchSimilarQuery`, `AppendMessageCommand`, `GetSessionHistoryQuery`.

**Weryfikacja:** integracyjne na SQLite + jeden test na Mongo z `$vectorSearch` (skipif brak feature flag).

### **Faza 10 — Tasker rekursja + multi-process orchestracja** ✅ ZAKOŃCZONA

Cel: pełna parytet z obecnym taskerem — tasker spawnuje sub_nody jako osobne procesy.

1. `TaskerStrategy.execute` — iteruje `graph.nodes`, dla każdego buduje argv (przez `command_builder`) wskazujące `framework/entrypoints/<mode>_entrypoint.py` + flagi, wywołuje `NodeProcessRunner.run`, agreguje wyniki w `NodeResult`.
2. Współbieżność (równoległe nody): `asyncio.gather` z `Semaphore(max_parallel)` z `Settings.max_parallel_nodes`.
3. Propagacja `workflow_id`/`envelope_id` jako env vars do sub-procesów.

**Weryfikacja:** `tests/e2e/cli/test_tasker_full_graph.py` — task z 3 nodami (agent + tool + worker stuby), asercja: wszystkie `NodeResult` zapisane, workflow status = COMPLETED.

### **Faza 11 — Audit / Logging / Observability** ✅ ZAKOŃCZONA

1. `EventPublisher` adapter `LoggingEventPublisher` (loguje JSON).
2. `EventPublisher` adapter `SqlAuditPublisher` (zapisuje do `audit_event`).
3. Composite publisher (`CompositeEventPublisher([logging, sql])`).
4. `infrastructure/logging/stdlib_logger.py` z strukturalnym formatem (JSON, correlation_id z contextvars).

**Weryfikacja:** unit testy publishera; e2e — po komendzie sprawdza wpis w `audit_event`.

### **Faza 12 — Outbox + EventBus persystentny** ✅ ZAKOŃCZONA

1. Transactional outbox: tabela `outbox_event`, zapis w tej samej transakcji co domain change.
2. `OutboxRelay` background task czytający outbox i publikujący do `EventBus`.

### **Faza 13 — Cleanup + dokumentacja** ✅ ZAKOŃCZONA

1. README z architekturą + diagramem zależności.
2. `docs/migration_notes.md` — mapowanie stary→nowy (z tabeli wyżej).
3. `docs/adr/` — ADR per kluczową decyzję (np. ADR-0001 dlaczego jeden BC; ADR-0002 strategie zamiast modułów per mode; ADR-0003 Mongo document-shape).
4. Skrypt smoke: `python -m shell_ddd.bootstrap.main smoke` — uruchamia import->workflow->route na 3 backendach po kolei.

---

## Kluczowe pliki referencyjne (z czego czerpać)

- Tasks/graph: `shell/task/task_repo/internal/_import_task_files.py`, `_apply_task_schema.py` → schema + import logic.
- Routing: `shell/module/router/router/internal/_run_router.py` + `_assert_*` → reguły routingu.
- Subprocess: `shell/component/process/process/internal/_run_process.py`, `process_command/internal/_init_process_command_*.py` → cmd construction.
- Memory init: `shell/app/app/internal/_init_memory_and_bus.py` → wzorzec session/engine.
- Config: `shell/component/config/`, `shell/component/placeholders/`, `shell/component/runtime/` → warstwy config + placeholders.

---

## Weryfikacja całościowa po wszystkich fazach

1. **Regresja behawioralna:** wybierz 3 przykłady (`workplace/example_tasks/example1.md`, jeden tasker scenariusz, jeden router scenariusz). Uruchom je w starym SHELL i w `shell_ddd` (oba na osobnym SQLite). Porównaj: exit code, zawartość `node_result.stdout/stderr/status`, `envelope.status` lifecycle, `audit_event` count.
2. **Wszystkie 3 backendy:** matrix CI — `pytest -m "integration"` z parametrem `--backend=sqlite|postgres|mongo`. Wszystkie zielone.
3. **Layering:** `tests/architecture/test_imports.py` (AST) — żaden plik z `domain/` nie importuje `application|infrastructure|framework|bootstrap`; analogicznie `application/` nie importuje `infrastructure|framework`; `infrastructure/` nie importuje `framework`.
4. **Coverage:** `domain >= 90%`, `application >= 85%`, `infrastructure >= 70%`.
5. **Lint/Type:** `ruff check` + `mypy --strict shell_ddd/domain shell_ddd/application` zielone.
6. **CLI parity:** dla każdego mode'a uruchom 1 reprezentatywne wywołanie z identycznymi argv jak obecne entrypointy i porównaj exit code + stdout.

---

## Decyzje

- **Jeden BC `shell`** — z świadomością, że agent/router/tasker/tool/worker mogłyby być osobnymi BC; tutaj są Strategy w jednym BC.
- **CLI + FastAPI**, oba przez ten sam CommandBus/QueryBus.
- **3 adaptery persistence** (SQLite, Postgres, Mongo) — Mongo z document-shape kompromisem.
- **SQLAlchemy 2.x async** dla obu SQL backendów (jeden zestaw mapperów/repo).
- **Standardowy styl pythonowy** — dataclasses + Protocol; **bez** slotów, bez `_x`/`x_`, bez `internal/_init_*.py`.
- **Stary kod pozostaje nietknięty** — `shell_ddd/` obok, w tym samym repo (jeden venv, jedno `pyproject.toml` można rozszerzyć dependency groups).
- **`UtilsPath` NIE jest portowany** — `pathlib.Path` bezpośrednio + cienki `filesystem/` helper.
- **`AppNode`/`Node`/`SubNode` jako folder-DOM NIE są portowane** — zastąpione przez `NodeWorkspace` (FS service) + czyste `Node` entity.

## Wykluczone ze scope (jawnie)

- Migracja istniejących danych z DB starego SHELL → nowego (nie ma jeszcze produkcji).
- Refaktor starego `shell/` (nietykany).
- HTTP autoryzacja w FastAPI (control plane lokalne; auth = osobna iteracja).
- Distributed tracing/OTel (faza późniejsza, poza tym planem).
- Frontend / UI.

## Dalsze rozważania

1. **Czy naprawdę 3 backendy persystencji?** Każdy = ~10 plików repo + UoW + migracje + suite testów + CI service. Rekomendacja: zacząć SQLite, dorzucić Postgres równolegle w fazie 7, Mongo dopiero gdy będzie realny use-case (możliwy stub).
2. **Czy CLI ma być nadal `typer`/argparse, czy reuse argparse identyczne jak teraz?** Rekomendacja: argparse 1:1 dla zachowania kompatybilności argv (zero ryzyka regresji wywołań subprocess między node'ami).
3. **Czy `Tasker` jako Strategy + subprocess, czy jako orchestrator in-process?** Obecnie subprocess (5 entrypointów). Rekomendacja: zachować subprocess (parity), ale dodać tryb in-process za feature flagiem (`SETTINGS.tasker_inprocess=True`) jako optymalizację testów.
