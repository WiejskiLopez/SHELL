# Sub-graf Orkiestracja — Architektura Enterprise Multi-Agent

**Cel:** System orkiestracji agentów, w którym każdy agent może być pojedynczym węzłem lub całym grafem (sub-grafem), a struktura wykonawcza tworzy rekurencyjne drzewo.  
**Maksymalna otwartość:** Każda warstwa definiuje interfejs (Protocol) — implementacje mogą być wymieniane, dodawane, pomijane.

---

## Spis treści

1. [Koncepcja rdzenia](#1-koncepcja-rdzenia)
2. [Model danych](#2-model-danych)
3. [Enterprise warstwy](#3-enterprise-warstwy)
4. [Przepływy wykonawcze](#4-przepływy-wykonawcze)
5. [Interfejsy (extension points)](#5-interfejsy-extension-points)
6. [Fazy implementacji](#6-fazy-implementacji)

---

## 1. Koncepcja rdzenia

```
┌──────────────────────────────────────────────────────────────┐
│  GraphExecution                                               │
│  ┌──────────┐    ┌──────────┐    ┌───────────────────────┐   │
│  │ AGENT    │───→│ TASKER   │───→│ AGENT                 │   │
│  │ (node)   │    │ (sub-graf)│    │ (node)                │   │
│  └──────────┘    └────┬─────┘    └───────────────────────┘   │
│                       │                                       │
│  ┌────────────────────▼────────────────────────────────────┐ │
│  │  GraphExecution (sub-graf)                               │ │
│  │  ┌──────────┐    ┌──────────┐    ┌──────────────────┐   │ │
│  │  │ TOOL     │───→│ AGENT    │───→│ END              │   │ │
│  │  └──────────┘    └──────────┘    └──────────────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘
```

**Tasker node = "foreign function call" do sub-grafu.**  
Nie nowy task_execution, nie child task. Po prostu wołasz inny graf jak funkcję, w ramach tego samego flow.

### Własności

| Property | Opis |
|---|---|
| **Rekurencja** | Każdy sub-graf może mieć własne taskery → drzewo o dowolnej głębokości |
| **Równoległość** | Sub-grafy równolegle przez istniejący PARALLEL+JOIN |
| **Izolacja** | Każdy sub-graf ma własny `GraphExecutionState` (scope'd JSONB) |
| **Kompozycja** | Tasker = jeden węzeł. Sub-graf = dowolnie złożony. To ta sama abstrakcja. |

---

## 2. Model danych

### GraphExecution — rozszerzenie

| Pole | Typ | Opis |
|---|---|---|
| `parent_graph_execution_id` | `GraphExecutionId \| None` | FK self → drzewo wykonawcze |
| `parent_tasker_node_execution_id` | `GraphNodeExecutionId \| None` | Który Tasker node w parent grafie mnie stworzył |
| `state_input` | `dict` (JSONB) | Stan wejściowy od rodzica |
| `state_output` | `dict` (JSONB) | Stan końcowy zwracany do rodzica |
| `depth` | `int` | Głębokość w drzewie (parent.depth + 1) |
| `timeout_at` | `datetime \| None` | Deadline execution |
| `correlation_id` | `str` | Distributed tracing — propagowany z parenta |
| `tags` | `dict` (JSONB) | Dowolne metadane (tenant, environment, owner, ...) |

### GraphNodeExecution — rozszerzenie

| Pole | Typ | Opis |
|---|---|---|
| `sub_graph_definition_id` | `str \| None` | FK → `graph_definition` (definicja pod-grafu) |
| `sub_graph_definition_version` | `int \| None` | Wersja definicji do użycia (snapshot versioning) |
| `timeout_seconds` | `int` | Timeout na wykonanie tego noda (override definicji) |
| `max_retries` | `int` | Maksymalna liczba retry |
| `retry_delay_seconds` | `int` | Opóźnienie między retry |

### Rozszerzalność przez `extra`

Każda encja ma pole `extra: dict` — JSONB. Służy jako nośnik dla dowolnych rozszerzeń:
- policy constraints (max_recursion_depth, max_parallel)
- security scopes
- custom metadata
- A/B testing flags

### Kluczowe: definicja vs execution

- **`GraphDefinition`** — szablon (blueprint). Może zmieniać się w czasie.
- **`GraphExecution`** — runtime snapshot zamaterializowany z definicji w momencie spawnu. Niezależny od `GraphDefinition` przez cały cykl życia.
- Drzewo wykonawcze operuje wyłącznie na `GraphExecution.id` — definicja po spawnie może być modyfikowana bez wpływu na działające execution.
- `state_input` / `state_output` to jawny kontrakt przekazywania danych między parent a child w drzewie.
- Wersja definicji (`sub_graph_definition_version`) jest rozwiązywana **tylko raz** — w momencie spawnu przez `SubGraphVersioning.resolve_definition()`.

---

## 3. Enterprise warstwy

Każda warstwa definiuje **interfejs (Protocol)**. Implementacje są wstrzykiwane przez DI.  
Brak implementacji = brak warstwy. System działa na rdzeniu.

```
┌─────────────────────────────────────────────────────────────┐
│  EXTENSION: Governance, Security, Observability, ...       │
├─────────────────────────────────────────────────────────────┤
│  CORE: GraphExecution, Tasker, SubGraphExecutionService    │
├─────────────────────────────────────────────────────────────┤
│  PERSISTENCE: SQL (SQLite/Postgres), InMemory              │
├─────────────────────────────────────────────────────────────┤
│  MESSAGING: Outbox/Inbox, EventBus (sync/async)            │
└─────────────────────────────────────────────────────────────┘
```

### 3.1 Resilience

```python
class SubGraphExecutionPolicy(Protocol):
    """Polityka wykonania sub-grafu."""

    async def on_timeout(
        self, graph_execution: GraphExecution, node: GraphNodeExecution
    ) -> Decision: ...

    async def on_failure(
        self, graph_execution: GraphExecution, node: GraphNodeExecution, reason: str
    ) -> Decision: ...

    async def on_depth_exceeded(
        self, graph_execution: GraphExecution, max_depth: int
    ) -> Decision: ...

class Decision:
    """Otwarta decyzja — extension point."""
    action: str  # "retry", "abort", "compensate", "skip", "fallback"
    payload: dict  # dowolne parametry
```

**Mechanizmy out-of-the-box:**
- Retry z backoffem (przez `max_retries` + `retry_delay_seconds`)
- Timeout na sub-graf (przez `timeout_at`)
- Circuit breaker: jeśli N sub-grafów z rzędu failuje → blokada
- Dead letter queue: sub-grafy które przekroczyły retry

### 3.2 Observability

```python
class SubGraphObserver(Protocol):
    """Nasłuchuje zdarzeń cyklu życia sub-grafu."""

    async def on_start(self, ctx: SubGraphContext): ...
    async def on_complete(self, ctx: SubGraphContext, result: ExecutionResult): ...
    async def on_fail(self, ctx: SubGraphContext, error: str): ...
    async def on_timeout(self, ctx: SubGraphContext): ...

class SubGraphContext:
    graph_execution_id: str
    parent_graph_execution_id: str | None
    depth: int
    correlation_id: str
    tags: dict
    started_at: datetime
    duration_ms: float | None  # po zakończeniu
```

**Built-in:** Audit event na każdą zmianę stanu (przez istniejący `audit_event`).  
**Extension:** OpenTelemetry tracing, Prometheus metrics, structured logging.

### 3.3 Governance

```python
class SubGraphGovernance(Protocol):
    """Ograniczenia i polityki."""

    async def can_spawn(
        self, parent: GraphExecution, definition_id: str, depth: int
    ) -> bool: ...

    async def max_parallel_sub_graphs(
        self, graph_execution: GraphExecution
    ) -> int: ...

    async def max_depth(
        self, root_graph_execution: GraphExecution
    ) -> int: ...

    async def token_budget(
        self, graph_execution: GraphExecution
    ) -> TokenBudget | None: ...
```

**Przykładowe implementacje:**
- `ConfigBasedGovernance` — proste limity z configu (max_depth=5, max_parallel=10)
- `LLMGovernance` — LLM decyduje czy sub-graf jest bezpieczny
- `TenantAwareGovernance` — różne limity dla różnych tenantów

### 3.4 Data Lineage

Każda zmiana w `GraphExecutionState` zawiera provenance:

```python
@dataclass
class StateChange:
    key: str
    value: object
    changed_by: str  # "graph_execution:<id>:node:<node_id>"
    changed_at: datetime
    correlation_id: str
```

`GraphExecutionState` rozszerzona o `_provenance: list[StateChange]` — append-only log.  
Pozwala odpowiedzieć: "Który agent w którym sub-grafie ustawił ten klucz?"

### 3.5 Compensation (Saga)

```python
class SubGraphCompensation(Protocol):
    """Cofa skutki sub-grafu."""

    async def compensate(
        self, graph_execution: GraphExecution, reason: str
    ) -> None: ...

    async def on_child_failed(
        self,
        parent_graph: GraphExecution,
        child_graph: GraphExecution,
        tasker_node: GraphNodeExecution,
    ) -> CompensationDecision: ...
```

**Strategie:**
- `NoOpCompensation` — brak cofania
- `RollbackStateCompensation` — przywraca `GraphExecutionState` sprzed sub-grafu
- `SagaCompensation` — woła `compensate` na każdym wykonanym węźle sub-grafu (od tyłu)

### 3.6 Security

```python
class SubGraphSecurity(Protocol):
    """Scope i permissions."""

    async def resolve_scope(
        self, parent: GraphExecution, sub_graph: GraphExecution
    ) -> Scope: ...

    async def filter_state(
        self, parent_state: dict, sub_graph: GraphExecution
    ) -> dict: ...
```

Scope określa co sub-graf widzi z parent state:
- `Scope.FULL` — cały stan rodzica
- `Scope.FILTERED` — tylko klucze z `allowed_keys`
- `Scope.ISOLATED` — sub-graf nie widzi żadnego stanu rodzica

### 3.7 Versioning

Sub-graf jest materializowany jako `GraphExecution` z `GraphDefinition` w momencie spawnu.
Drzewo operuje na `GraphExecution` — definicja może się zmienić w trakcie, działające execution jest zamrożone.

```python
class SubGraphVersioning(Protocol):
    """Wybiera wersję definicji przy spawnie sub-grafu."""

    async def resolve_definition(
        self, definition_id: str, version: int | None, parent: GraphExecution
    ) -> GraphDefinition: ...
```

**Strategie (dotyczą tylko momentu spawnu):**
- `PinVersionStrategy` — konkretna wersja z `sub_graph_definition_version` (jeśli None → Latest)
- `LatestVersionStrategy` — zawsze najnowsza wersja w momencie spawnu
- `SnapshotStrategy` — zapisuje całą definicję w `GraphExecution.extra` (full freeze)

**Po spawnie:** `GraphExecution` jest niezależny od `GraphDefinition`. Zmiana definicji nie wpływa na działające execution. Nie ma "dryfu" — execution to zamrożony snapshot.

---

## 4. Przepływy wykonawcze

### 4.1 Tasker node → sub-graf (sekwencyjny)

```
Graph_1: [AGENT_1] ──SEQUENCE──→ [TASKER_A] ──SEQUENCE──→ [AGENT_2]
                                    │
                                    │ sub_graph_definition_id = "gd_debt_analysis"
                                    ▼
                              Graph_2: [TOOL] ──→ [AGENT] ──→ [END]
```

1. `Graph_1`: AGENT_1 → SUCCESS
2. `workflow.advance_to(TASKER_A)` → `GraphNodeExecutionRequestedEvent`
3. `GraphNodeExecutionWorker`:
   - ładuje TASKER_A node
   - widzi `mode=TASKER`, `sub_graph_definition_id="gd_debt_analysis"`
   - NIE uruchamia subprocessu
   - woła `SubGraphExecutionService.spawn()`
4. `SubGraphExecutionService`:
   - **Governance**: `can_spawn(parent, def_id, depth+1)` → jeśli nie, fail tasker node
   - **Security**: `resolve_scope(parent, sub_graph)` → określa scope
   - **Security**: `filter_state(parent_state, sub_graph)` → filtruje stan
   - **Versioning**: `resolve_definition(def_id, version, parent)` → wybiera definicję
   - tworzy `GraphExecution` (Graph_2) z `parent_graph_execution_id=Graph_1.id`
   - zapisuje `state_input = filtered_state`
   - emituje `SubGraphExecutionStartedEvent`
   - **Observer**: `on_start(ctx)`
   - **Observability**: zapisuje `correlation_id`, `depth`, `tags`
   - uruchamia execution Graph_2 (pierwszy node)
5. TASKER_A zostaje w `IN_PROGRESS` — `workflow.cursor` wciąż wskazuje na TASKER_A
6. Graph_2 wykonuje się (może mieć własne taskery, planery, etc.)
7. Graph_2 kończy się → `GraphExecutionCompletedEvent`
8. `SubGraphCompletedHandler`:
   - widzi `parent_graph_execution_id=Graph_1.id`
   - ładuje Graph_1 + TASKER_A
   - ładuje final `GraphExecutionState` z Graph_2
   - **Compensation**: jeśli fail → `on_child_failed(parent, child, tasker_node)`
   - **Observer**: `on_complete(ctx, result)`
   - zapisuje `state_output` jako `TASKER_A.output_payload`
   - oznacza TASKER_A jako SUCCESS
   - woła `workflow.record_graph_node_execution_result(TASKER_A, SUCCESS)`
   - → `GraphNodeExecutionCompletedEvent`
9. `GraphNodeExecutionResultHandler` (Cycle B):
   - sprawdza outgoing transitions TASKER_A → znajduje AGENT_2
   - `workflow.advance_to(AGENT_2)`

**Żadnego SUSPENDED. Żadnych child task_execution. Czyste sub-grafy.**

### 4.2 Równoległe sub-grafy (przez istniejący PARALLEL + JOIN)

```
Graph_1: [AGENT_1] ──PARALLEL──→ [TASKER_A] ──┐
                         ├─────→ [TASKER_B] ──┼──JOIN──→ [AGENT_2]
                         └─────→ [TASKER_C] ──┘
```

To działa na istniejącym mechanizmie `ParallelGroup` + `JoinCounter`.  
Zero zmian w logice parallel/join. Każdy TASKER spawnuje swój sub-graf niezależnie.  
JOIN czeka aż wszystkie sub-grafy skończą.

**Governance check:** `max_parallel_sub_graphs(parent)` → jeśli limit przekroczony, fail.

### 4.3 Planner (opcjonalna dynamiczna mutacja grafu)

```
Graph: [AGENT] ──→ [PLANNER] ──→ [END]

  Agent: "Znalazlem problem. Potrzebuje analizy X i Y."
  Planner (LLM): dodaje:
    [TASKER_A: sub_graph="analyze_x"]
    [TASKER_B: sub_graph="analyze_y"]
    transitions: PLANNER ──PARALLEL──→ TASKER_A
                 PLANNER ──PARALLEL──→ TASKER_B
                 TASKER_A ──JOIN──→ PLANNER
                 TASKER_B ──JOIN──→ PLANNER
  Planner: "Done. Continuing..."
  Wykonanie: → TASKER_A → równolegle TASKER_B → JOIN → PLANNER (drugi raz)
  Planner (drugi raz): "Wszystkie analizy gotowe. Routing do END."
```

---

## 5. Interfejsy (extension points)

Każdy interfejs to `Protocol`. Domyślne implementacje są puste lub minimalistyczne.  
Można je wymieniać przez DI — bez zmiany kodu rdzenia.

```python
# ── extension/ ──
# sub_graph_policy.py
class SubGraphExecutionPolicy(Protocol): ...

# sub_graph_observer.py
class SubGraphObserver(Protocol): ...

# sub_graph_governance.py
class SubGraphGovernance(Protocol): ...

# sub_graph_compensation.py
class SubGraphCompensation(Protocol): ...

# sub_graph_security.py
class SubGraphSecurity(Protocol): ...

# sub_graph_versioning.py
class SubGraphVersioning(Protocol): ...
```

**Domyślne implementacje** (wbudowane, można podmienić):

| Interfejs | Domyślna implementacja |
|---|---|
| `SubGraphExecutionPolicy` | `RetryPolicy(max_retries=0, timeout=None)` |
| `SubGraphObserver` | `LoggingObserver(logger)` — loguje start/complete/fail |
| `SubGraphGovernance` | `PermissiveGovernance()` — wszystko dozwolone |
| `SubGraphCompensation` | `NoOpCompensation()` — brak cofania |
| `SubGraphSecurity` | `FullAccessSecurity()` — pełny scope, brak filtra |
| `SubGraphVersioning` | `LatestVersionStrategy()` — zawsze najnowsza |

---

## 6. Fazy implementacji

### Phase 1: Data Model (otwartość od podstaw)

| Plik | Zmiana |
|---|---|
| `domain/execution/aggregates/graph_execution/graph_execution.py` | Dodać `_parent_graph_execution_id`, `_parent_tasker_node_execution_id`, `_state_input`, `_state_output`, `_depth`, `_timeout_at`, `_correlation_id`, `_tags` |
| `domain/execution/entities/graph_node_execution.py` | Dodać `_sub_graph_definition_id`, `_sub_graph_definition_version`, `_timeout_seconds`, `_max_retries`, `_retry_delay_seconds` |
| `infrastructure/execution/persistence/sql/models/graph_execution.py` | Dodać kolumny |
| `infrastructure/execution/persistence/sql/models/graph_node_execution.py` | Dodać kolumny |
| `infrastructure/platform/persistence/sql/mappers/__init__.py` | Zmapować nowe pola |
| `application/execution/dto/graph_execution.py` | Dodać pola do DTO |
| `application/execution/dto/graph_node_execution.py` | Dodać pola do DTO |

### Phase 2: Sub-graph execution

| Plik | Odpowiedzialność |
|---|---|
| `domain/execution/events/sub_graph_execution_started_event.py` | Event: sub-graf wystartował |
| `domain/execution/events/sub_graph_execution_completed_event.py` | Event: sub-graf skończył |
| `domain/execution/services/sub_graph_execution_service.py` | Domain service: tworzy sub-graf, linkuje, emituje event |
| `domain/execution/services/sub_graph_execution_service.py` | Extension points: deleguje do Policy, Governance, Security, Versioning, Observer |
| `application/execution/event_handlers/sub_graph_completed_handler.py` | Handler: merge output, oznacz tasker node jako done, advance parent workflow |

**Modyfikacje:**

| Plik | Zmiana |
|---|---|
| `application/execution/event_handlers/graph_node_execution_worker.py` | Wykryć `mode=TASKER + sub_graph_definition_id` → delegować do `SubGraphExecutionService` zamiast subprocessu |
| `bootstrap/platform/container/*` | Zarejestrować nowe serwisy i handlery |

### Phase 3: Extension points (interfejsy)

| Plik | Opis |
|---|---|
| `domain/execution/ports/sub_graph_policy.py` | Protocol: SubGraphExecutionPolicy |
| `domain/execution/ports/sub_graph_observer.py` | Protocol: SubGraphObserver |
| `domain/execution/ports/sub_graph_governance.py` | Protocol: SubGraphGovernance |
| `domain/execution/ports/sub_graph_compensation.py` | Protocol: SubGraphCompensation |
| `domain/execution/ports/sub_graph_security.py` | Protocol: SubGraphSecurity |
| `domain/execution/ports/sub_graph_versioning.py` | Protocol: SubGraphVersioning |
| `infrastructure/default_implementations/...` | Domyślne implementacje (Permissive, NoOp, etc.) |

### Phase 4: Planner (opcjonalny)

| Plik | Opis |
|---|---|
| `domain/platform/value_objects/mode.py` | Dodać `PLANNER = "planner"` |
| `application/execution/strategies/graph_node_execution_strategy/planner_strategy.py` | Strategy: uruchamia LLM jako subprocess |
| `domain/execution/aggregates/graph_execution/graph_execution.py` | Dodać `add_node()`, `add_transition()` (runtime mutation) |
| `application/execution/event_handlers/planner_response_handler.py` | Handler: parsuje output Planera, modyfikuje graf, routuje |
| `framework/execution/entrypoints/planner_entrypoint.py` | Entrypoint dla subprocessu |
| `application/execution/strategies/graph_node_execution_strategy/registry.py` | Zarejestrować `PlannerStrategy` |

---

## Zasady architektoniczne

1. **Brak SUSPENDED** — parent graph czeka bo cursor nie rusza. Tasker node jest `IN_PROGRESS` dopóki sub-graf nie skończy.

2. **Brak child task_execution** — sub-graf to osobny `GraphExecution`, nie osobny `TaskExecution`.

3. **Stan przekazywany explicit** — parent → `state_input` → sub-graf → `state_output` → `TaskerNode.output_payload`.

4. **Równoległość przez istniejący PARALLEL+JOIN** — sub-grafy równolegle korzystają z `ParallelGroup` i `JoinCounter`. Zero nowej logiki.

5. **Tasker node = "foreign function call"** — nie spawnuje procesu, spawnuje sub-graf.

6. **Planner opcjonalny** — 80% grafów ma stałą strukturę i nie potrzebuje runtime mutation.

7. **Extension points = Protocols** — każda warstwa enterprise to interfejs. Brak implementacji = brak warstwy.

8. **Wszystko przez `extra`** — każde rozszerzenie danych przez JSONB `extra` na encjach. Zero migracji dla nowych pól.

9. **Open/Closed** — rdzeń zamknięty dla modyfikacji, otwarty dla rozszerzeń przez DI.


Agent output (JSON) 
  └→ request_new_tasks: [{sub_graph_definition_id, reason, state_input}]
       └→ GraphNodeExecutionResultHandler (Cycle B)
            └→ OutputInterpreter (Protocol → AgentOutputInterpreter)
                 └→ OutputDecision.spawn_sub_graphs()
                      └→ SubGraphExecutionService
                           ├── Governance: can_spawn?
                           ├── Versioning: resolve_definition
                           ├── Security: filter_state
                           ├── Spawn: child TaskExecution + GraphExecution + Workflow
                           └── Observer: on_start
                                └→ SubGraph runs independently
                                     └→ WorkflowCompletedEvent
                                          └→ SubGraphCompletedHandler
                                               └→ Mark Tasker node SUCCESS
                                                    └→ Normal advance (Cycle B)