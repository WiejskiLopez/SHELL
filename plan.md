# Plan migracji domeny do DOMAINV3

> Źródło wymagań: `DOMAINV3.md`
> Konwencje: `.agents/skills/shell-architecture/`
> Subdomeny: `execution`, `user`, `projekt`, `scheduling` (nowa)

---

## Zależności między etapami

```
ETAP 0 (VO + Eventy) ──► ETAP 1 (AgentExec + Transition) ──► ETAP 2 (GraphNodeExec)
                                  │                                    │
                                  └────────────────────────────────────┘
                                                       │
                                                       ▼
                                                  ETAP 3 (GraphExec)
                                                       │
                                                       ▼
                                                  ETAP 4 (TaskExec)
                                                       │
                                          ┌────────────┴────────────┐
                                          ▼                         ▼
                              ETAP 5 (Session + Workflow)    ETAP 6 (User + Project)
                                          │                         │
                                          └────────────┬────────────┘
                                                       ▼
                                              ETAP 7 (AgentConfigExec)
                                                       │
                                                       ▼
                                              ETAP 8 (Scheduler)
                                                       │
                                                       ▼
                                              ETAP 9 (Czystki)

Infrastruktura (ORM, migracje, repo) + Handlery + Testy — per agregat, równolegle z etapem macierzystym.
```

---

## Legenda

| Znacznik | Znaczenie |
|----------|-----------|
| `[NEW]` | Nowy plik/katalog do utworzenia |
| `[MOD]` | Istniejący plik do modyfikacji |
| `[DEL]` | Plik do usunięcia |
| `[MOV]` | Przeniesienie logiki z A do B |
| `✓` | Kryterium weryfikacji etapu |

---

## ETAP 0 — VALUE OBJECTS + DOMAIN EVENTS

**Czas:** ~2h | **Zależności:** brak | **Ryzyko:** niskie (tylko nowe pliki)

Wszystkie nowe VO i eventy — żaden istniejący kod nie jest ruszany.

### 0.1 Nowe ID-ki

Katalog: `shell/domain/execution/aggregates/<agregat>/`

| # | Plik | Klasa | Wzorzec |
|---|------|-------|---------|
| 0.1.1 | `[NEW]` `agent_execution/agent_execution_id.py` | `AgentExecutionId` | frozen dataclass, `value: str`, UUID |
| 0.1.2 | `[NEW]` `agent_config_execution/agent_config_execution_id.py` | `AgentConfigExecutionId` | jw. |
| 0.1.3 | `[NEW]` `graph_node_transition_execution/graph_node_transition_execution_id.py` | `GraphNodeTransitionExecutionId` | jw. |
| 0.1.4 | `[NEW]` `agent_execution/agent_skill_execution_id.py` | `AgentSkillExecutionId` | jw. |
| 0.1.5 | `[NEW]` `session/session_id.py` | `SessionId` (jeśli nie istnieje) | jw. |

Dla subdomen `user` i `projekt`:

| # | Plik | Klasa |
|---|------|-------|
| 0.1.6 | `[NEW]` `shell/domain/user/value_objects/user_id.py` | `UserId` |
| 0.1.7 | `[NEW]` `shell/domain/projekt/value_objects/project_id.py` | `ProjectId` |

> **✓ Weryfikacja:** `import` każdego ID działa, `isinstance(UserId("..."), UserId)` → True.

### 0.2 Nowe statusy / enumy

| # | Plik | Klasa | Wartości |
|---|------|-------|----------|
| 0.2.1 | `[NEW]` `execution/value_objects/task_execution_status.py` | `TaskExecutionStatus` (StrEnum) | `CREATED`, `IN_PROGRESS`, `COMPLETED`, `FAILED`, `EXHAUSTED` |
| 0.2.2 | `[NEW]` `execution/value_objects/graph_execution_status.py` | `GraphExecutionStatus` (StrEnum) | `PENDING`, `PLANNING`, `EXECUTING`, `VERIFYING`, `COMPLETED`, `FAILED` |
| 0.2.3 | `[NEW]` `execution/value_objects/graph_node_execution_status.py` | `GraphNodeExecutionStatus` (StrEnum) | `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`, `TIMED_OUT` |
| 0.2.4 | `[NEW]` `execution/value_objects/transition_status.py` | `TransitionStatus` (StrEnum) | `EVALUATED`, `TAKEN`, `SKIPPED` |
| 0.2.5 | `[NEW]` `execution/value_objects/node_role.py` | `NodeRole` (StrEnum) | `PLANNER`, `AGENT`, `TOOLS`, `VERIFIER` |
| 0.2.6 | `[NEW]` `execution/value_objects/edge_type.py` | `EdgeType` (StrEnum) | `SEQUENCE`, `CONDITIONAL`, `LOOP`, `SPAWN_SUBGRAPH`, `ERROR_HANDLER`, `TIMEOUT`, `DEFAULT` |
| 0.2.7 | `[NEW]` `execution/value_objects/session_status.py` | `SessionStatus` (StrEnum) | `OPEN`, `CLOSED` |
| 0.2.8 | `[NEW]` `execution/value_objects/workflow_status.py` | `WorkflowStatus` (StrEnum) | `ACTIVE`, `COMPLETED`, `ABORTED` |
| 0.2.9 | `[NEW]` `execution/value_objects/user_status.py` | `UserStatus` (StrEnum) | `ACTIVE`, `DISABLED` |
| 0.2.10 | `[NEW]` `execution/value_objects/project_status.py` | `ProjectStatus` (StrEnum) | `ACTIVE`, `ARCHIVED` |

> **✓ Weryfikacja:** każdy StrEnum ma poprawne wartości, `EdgeType` nie zawiera `PARALLEL` ani `JOIN`.

### 0.3 Value objects domenowe

| # | Plik | Klasa | Opis |
|---|------|-------|------|
| 0.3.1 | `[NEW]` `execution/value_objects/graph_depth.py` | `GraphDepth` | int >= 0 |
| 0.3.2 | `[NEW]` `execution/value_objects/max_subgraph_depth.py` | `MaxSubgraphDepth` | int >= 1, default 5 |
| 0.3.3 | `[NEW]` `execution/value_objects/planning_cycle.py` | `PlanningCycle` | int >= 0 |
| 0.3.4 | `[NEW]` `execution/value_objects/max_planning_cycles.py` | `MaxPlanningCycles` | int >= 1 |
| 0.3.5 | `[NEW]` `execution/value_objects/node_order.py` | `NodeOrder` | int >= 0 |
| 0.3.6 | `[NEW]` `execution/value_objects/agent_config.py` | `AgentConfig` | frozen dataclass: `model`, `temperature`, `max_tokens`, `top_p` |

> **✓ Weryfikacja:** `GraphDepth(-1)` rzuca `ValueError`. `MaxSubgraphDepth()` → default=5.

### 0.4 Refaktor istniejących VO

| # | Plik | Zmiana |
|---|------|--------|
| 0.4.1 | `[MOD]` `platform/value_objects/transition_type.py` — `TransitionType` | Usuń `parallel`, `join`. Dodaj `spawn_subgraph`. Brakujące typy już ma (`sequence`, `conditional`, `error_handler`, `loop`, `timeout`, `default`). |
| 0.4.2 | `[MOD]` `platform/value_objects/status.py` — `Status` | Oznacz jako `@deprecated` — zastąpiony przez dedykowane statusy per agregat (0.2.1–0.2.3, 0.2.7, 0.2.8). **Nie usuwaj jeszcze** — używany przez istniejący Workflow. |
| 0.4.3 | `[MOD]` `platform/value_objects/mode.py` — `Mode` | Oznacz jako `@deprecated` — zastąpiony przez `NodeRole` (0.2.5). **Nie usuwaj jeszcze** — używany przez GraphNodeExecution. |

> **✓ Weryfikacja:** `TransitionType` nie ma `parallel`/`join`, ma `spawn_subgraph`.

### 0.5 Nowe eventy domenowe — TaskExecution (§13.1)

Katalog: `shell/domain/execution/aggregates/task_execution/events/`

| # | Plik `[NEW]` | Klasa | Payload |
|---|-------------|-------|---------|
| 0.5.1 | `task_execution_started_event.py` | `TaskExecutionStartedEvent` | `task_execution_id` |
| 0.5.2 | `task_execution_completed_event.py` | `TaskExecutionCompletedEvent` | `task_execution_id`, `output` |
| 0.5.3 | `task_execution_failed_event.py` | `TaskExecutionFailedEvent` | `task_execution_id`, `reason` |
| 0.5.4 | `task_execution_exhausted_event.py` | `TaskExecutionExhaustedEvent` | `task_execution_id`, `current_cycle`, `max_cycles` |

> Zachować istniejący `TaskExecutionCreatedEvent`.

### 0.6 Nowe eventy domenowe — GraphExecution (§13.2)

Katalog: `shell/domain/execution/aggregates/graph_execution/events/`

| # | Plik `[NEW]` | Klasa | Payload |
|---|-------------|-------|---------|
| 0.6.1 | `graph_execution_created_event.py` | `GraphExecutionCreatedEvent` | `graph_execution_id`, `task_execution_id`, `parent_graph_execution_id`, `goal`, `depth` |
| 0.6.2 | `graph_planning_started_event.py` | `GraphPlanningStartedEvent` | `graph_execution_id` |
| 0.6.3 | `graph_spawned_event.py` | `GraphSpawnedEvent` | `parent_id`, `child_id`, `goal` |
| 0.6.4 | `graph_planned_event.py` | `GraphPlannedEvent` | `graph_execution_id`, `plan` |
| 0.6.5 | `sub_graph_settled_event.py` | `SubGraphSettledEvent` | `parent_id`, `children_results: list[{id, status, result}]` |
| 0.6.6 | `graph_execution_completed_event.py` | `GraphExecutionCompletedEvent` | `graph_execution_id`, `verifier_result` |
| 0.6.7 | `graph_execution_failed_event.py` | `GraphExecutionFailedEvent` | `graph_execution_id`, `reason` |

> Era „komunikacyjnych” — emitowane z agregatu GraphExecution przy przejściach stanu.

### 0.7 Nowe eventy domenowe — GraphNodeExecution (§13.3)

Katalog: `shell/domain/execution/aggregates/graph_node_execution/events/`

| # | Plik `[NEW]` | Klasa | Payload |
|---|-------------|-------|---------|
| 0.7.1 | `graph_node_execution_started_event.py` | `GraphNodeExecutionStartedEvent` | `node_id`, `role` |
| 0.7.2 | `graph_node_execution_completed_event.py` | `GraphNodeExecutionCompletedEvent` | `node_id`, `role`, `result` |
| 0.7.3 | `graph_node_execution_failed_event.py` | `GraphNodeExecutionFailedEvent` | `node_id`, `role`, `error` |

> Era „komunikacyjnych” — co node zrobił, bez decyzji routingowych.

### 0.8 Nowe eventy domenowe — Transition/Edge (§13.4)

Katalog: `shell/domain/execution/aggregates/graph_node_transition_execution/events/`

| # | Plik `[NEW]` | Klasa | Payload |
|---|-------------|-------|---------|
| 0.8.1 | `transition_condition_evaluated_event.py` | `TransitionConditionEvaluatedEvent` | `transition_id`, `source_node_id`, `condition_result` |
| 0.8.2 | `transition_taken_event.py` | `TransitionTakenEvent` | `transition_id`, `source_node_id`, `target_node_id` |
| 0.8.3 | `transition_looped_event.py` | `TransitionLoopedEvent` | `transition_id`, `source_node_id`, `iteration` |
| 0.8.4 | `transition_error_handled_event.py` | `TransitionErrorHandledEvent` | `transition_id`, `failed_node_id`, `handler_node_id` |
| 0.8.5 | `transition_timed_out_event.py` | `TransitionTimedOutEvent` | `transition_id`, `node_id`, `handler_node_id` |

> Era „decyzyjnych” — Edge zdecydował o routingu.

### 0.9 Nowe eventy domenowe — Session + Workflow

| # | Plik `[NEW]` | Klasa | Payload |
|---|-------------|-------|---------|
| 0.9.1 | `session/events/session_opened_event.py` | `SessionOpenedEvent` | `session_id`, `user_id`, `project_id` |

> Istniejące Workflow eventy (`WorkflowStartedEvent`, `WorkflowCompletedEvent`, `WorkflowFailedEvent`) — zachować. Dostosować payload w etapie 5.

> **✓ Weryfikacja etapu 0:** Wszystkie 35+ nowych plików istnieje. `python -c "from shell.domain.execution.value_objects.task_execution_status import TaskExecutionStatus; print(TaskExecutionStatus.CREATED)"` działa. Żaden istniejący test nie jest złamany.

---

## ETAP 1 — AGENT EXECUTION + GRAPH NODE TRANSITION (nowe agregaty-liście)

**Czas:** ~4h | **Zależności:** ETAP 0 | **Ryzyko:** niskie (tylko nowe pliki, nic nie jest ruszane)

Agregaty na dole hierarchii — nie mają dzieci, nie blokują innych.

### 1.1 AgentExecution — struktura katalogu

```
[NEW] shell/domain/execution/aggregates/agent_execution/
  ├── __init__.py
  ├── agent_execution.py              # AggregateRoot
  ├── agent_execution_id.py           # VO (z ETAPU 0.1.1)
  ├── entities/
  │   ├── __init__.py
  │   └── agent_skill_execution.py    # Child entity
  ├── value_objects/ (puste lub agent_config_snapshot.py)
  ├── events/ (puste — agent nie emituje własnych eventów)
  ├── ports/
  │   ├── __init__.py
  │   └── agent_execution_repository.py
  ├── exceptions/
  │   ├── __init__.py
  │   └── agent_execution_not_found.py
  └── services/ (puste)
```

### 1.2 AgentExecution — agregat

```python
# agent_execution.py
class AgentExecution(AggregateRoot[AgentExecutionId]):
    __slots__ = ("_graph_node_execution_id", "_config_snapshot", "_skills")

    _graph_node_execution_id: GraphNodeExecutionId
    _config_snapshot: AgentConfig
    _skills: list[AgentSkillExecution]

    # Factory: tworzony gdy GraphNodeExecution z role=AGENT
    @classmethod
    def for_node(cls, id_, node_id, config_snapshot, skills, now):
        instance = cls(id_)
        instance._graph_node_execution_id = node_id
        instance._config_snapshot = config_snapshot
        instance._skills = [AgentSkillExecution(...) for ... in skills]
        return instance
```

Pola:
- `id: AgentExecutionId`
- `graph_node_execution_id: GraphNodeExecutionId` — relacja 1:1 z nodem AGENT
- `config_snapshot: AgentConfig` — kopia configu LLM z `AgentConfigExecution` (audyt)
- `skills: list[AgentSkillExecution]` — append-only archiwum skili użytych przy wykonaniu

> **Brak FSM** — AgentExecution jest znacznikiem + archiwum. Nie ma własnych przejść stanu.

### 1.3 AgentSkillExecution — encja

```python
# entities/agent_skill_execution.py
@dataclass(frozen=True)
class AgentSkillExecution:
    id: AgentSkillExecutionId
    agent_execution_id: AgentExecutionId
    payload: dict
    created_at: datetime
```

Struktura: `{id, agent_execution_id (FK CASCADE), payload: JSON, created_at}`. Append-only.

### 1.4 AgentExecutionRepository — port

```python
# ports/agent_execution_repository.py
class AgentExecutionRepository(Protocol):
    async def get_by_id(self, id_: AgentExecutionId) -> AgentExecution | None: ...
    async def get_by_node_execution_id(self, node_id: GraphNodeExecutionId) -> AgentExecution | None: ...
    async def save(self, agent_execution: AgentExecution) -> None: ...
```

### 1.5 GraphNodeTransitionExecution — struktura katalogu

```
[NEW] shell/domain/execution/aggregates/graph_node_transition_execution/
  ├── __init__.py
  ├── graph_node_transition_execution.py      # AggregateRoot
  ├── graph_node_transition_execution_id.py   # VO (z ETAPU 0.1.3)
  ├── entities/ (puste)
  ├── value_objects/
  │   ├── __init__.py
  │   └── spawn_spec.py                       # VO: goal, skills, target_role
  ├── events/
  │   ├── __init__.py
  │   ├── transition_condition_evaluated_event.py   # ETAP 0.8.1
  │   ├── transition_taken_event.py                 # ETAP 0.8.2
  │   ├── transition_looped_event.py                # ETAP 0.8.3
  │   ├── transition_error_handled_event.py         # ETAP 0.8.4
  │   └── transition_timed_out_event.py             # ETAP 0.8.5
  ├── ports/
  │   ├── __init__.py
  │   └── graph_node_transition_execution_repository.py
  └── exceptions/
      ├── __init__.py
      └── invalid_transition.py
```

### 1.6 GraphNodeTransitionExecution — agregat

```python
class GraphNodeTransitionExecution(AggregateRoot[GraphNodeTransitionExecutionId]):
    __slots__ = (
        "_graph_execution_id", "_source_node_execution_id",
        "_target_node_execution_id", "_spawn_spec",
        "_edge_type", "_condition_expression", "_max_iterations",
        "_status", "_current_iteration",
    )

    _graph_execution_id: GraphExecutionId
    _source_node_execution_id: GraphNodeExecutionId
    _target_node_execution_id: GraphNodeExecutionId | None   # None dla SPAWN_SUBGRAPH
    _spawn_spec: SpawnSpec | None                             # tylko dla SPAWN_SUBGRAPH
    _edge_type: EdgeType
    _condition_expression: str | None                         # tylko dla CONDITIONAL
    _max_iterations: int | None                               # tylko dla LOOP
    _status: TransitionStatus
    _current_iteration: int                                   # tylko dla LOOP
```

FSM:
```
[EVALUATED] ──take()──► [TAKEN]    (SEQUENCE, CONDITIONAL true, DEFAULT)
[EVALUATED] ──skip()──► [SKIPPED]  (CONDITIONAL false)
[TAKEN]     ──loop()──► [EVALUATED] (LOOP, iteration < max)
```

Emituje eventy decyzyjne:
- `take()` → `TransitionTakenEvent`
- `evaluate_condition(result)` → `TransitionConditionEvaluatedEvent` + `take()`/`skip()`
- `loop()` → `TransitionLoopedEvent`
- `handle_error()` → `TransitionErrorHandledEvent`
- `handle_timeout()` → `TransitionTimedOutEvent`

### 1.7 SpawnSpec — VO

```python
@dataclass(frozen=True)
class SpawnSpec:
    goal: str
    skills: tuple[dict, ...]          # skille do przekazania sub-grafowi
    target_role: NodeRole | None      # None = domyślny PLANNER
```

### 1.8 GraphNodeTransitionExecutionRepository — port

```python
class GraphNodeTransitionExecutionRepository(Protocol):
    async def get_by_id(self, id_: GraphNodeTransitionExecutionId) -> GraphNodeTransitionExecution | None: ...
    async def list_by_graph_execution_id(self, graph_execution_id: GraphExecutionId) -> list[GraphNodeTransitionExecution]: ...
    async def list_outgoing_for_node(self, node_id: GraphNodeExecutionId) -> list[GraphNodeTransitionExecution]: ...
    async def save(self, transition: GraphNodeTransitionExecution) -> None: ...
```

> **✓ Weryfikacja etapu 1:** Oba agregaty kompilują się. Można utworzyć `AgentExecution.for_node(...)` i `GraphNodeTransitionExecution` z każdym `EdgeType`. Transition FSM przechodzi poprawne ścieżki, rzuca wyjątek przy niepoprawnych (np. `take()` na już `TAKEN`). Testy jednostkowe obu agregatów przechodzą.

---

## ETAP 2 — GRAPH NODE EXECUTION (refaktor)

**Czas:** ~5h | **Zależności:** ETAP 1 | **Ryzyko:** średnie (istniejący agregat — zmiana pól, FSM, eventów)

### 2.1 Dodaj FSM do GraphNodeExecution

Obecnie: bezstatusowy kontener.  
Docelowo (§10.1):

```python
class GraphNodeExecution(AggregateRoot[GraphNodeExecutionId]):
    __slots__ = (
        "_graph_execution_id", "_role", "_order", "_status",
        "_state_inputs", "_state_outputs",
        # pola legacy do usunięcia w ETAPIE 9
    )

    _graph_execution_id: GraphExecutionId
    _role: NodeRole
    _order: NodeOrder
    _status: GraphNodeExecutionStatus
    _state_inputs: list[GraphNodeExecutionStateInput]    # append-only
    _state_outputs: list[GraphNodeExecutionStateOutput]  # append-only
```

FSM:
```
[PENDING] ──start()──► [RUNNING] ──complete(result)──► [COMPLETED]
                         │
                         ├──fail(error)──► [FAILED]
                         └──timeout()───► [TIMED_OUT]
```

### 2.2 Metody agregatu

| Metoda | Przejście | Emitowany event |
|--------|-----------|-----------------|
| `start()` | PENDING → RUNNING | `GraphNodeExecutionStartedEvent` |
| `complete(result)` | RUNNING → COMPLETED | `GraphNodeExecutionCompletedEvent` |
| `fail(error)` | RUNNING → FAILED | `GraphNodeExecutionFailedEvent` |
| `timeout()` | RUNNING → TIMED_OUT | `GraphNodeExecutionTimedOutEvent` |

- `complete(result)`: result zapisywany jako nowy `GraphNodeExecutionStateOutput` (append-only).
- **Node NIE decyduje o routingu** (D2). Routing to domena Edge'a (ETAP 1).

### 2.3 GraphNodeExecutionStateInput / StateOutput — encje

Obecnie istnieją jako child entities w `graph_node_execution/entities/`.  
Zmiany:
- `[MOD]` Zmień nazwy z `GraphNodeExecutionStateInput` → `GraphNodeExecutionStateInput` (zachować — już ma dobrą nazwę po poprawkach w DOMAINV3.md)
- `[MOD]` Usuń `is_current` — append-only, bez flagi. Najnowszy = ostatni wiersz.
- `[MOD]` Pola: `id`, `graph_node_execution_id (FK CASCADE)`, `payload: JSON`, `created_at`.

### 2.4 Refaktor istniejących pól

Obecny `GraphNodeExecution` ma ~25 pól (`position`, `mode`, `node_type`, `command`, `timeout`, `retries`, `log_level`, `max_step`, `no_ask_user`, `autopilot`, `task_execution_id`, `source_dir`, `status_initial`, `timeout_seconds`, `max_retries`, `retry_delay_seconds`, `model`, `role`).

Docelowo z V3: tylko `role`, `order`, `status`, state I/O kolekcje.

**Strategia:** dodaj nowe pola (FSM, role, order, state I/O), oznacz stare jako `@deprecated`. Usunięcie starych → ETAP 9 (po przepięciu handlerów).

### 2.5 Podłączenie AgentExecution (relacja 1:1)

W metodzie `start()`:
```python
if self._role == NodeRole.AGENT:
    # AgentExecution tworzony przez handler, nie przez sam node
    # Node tylko emituje GraphNodeExecutionStartedEvent z role=AGENT
    # Handler tworzy AgentExecution na podstawie tego eventu
```

> Node nie tworzy `AgentExecution` sam — to odpowiedzialność handlera (separation of concerns).

### 2.6 Aktualizacja portu repozytorium

```python
class GraphNodeExecutionRepository(Protocol):
    async def get_by_id(self, id_: GraphNodeExecutionId) -> GraphNodeExecution | None: ...
    async def list_by_graph_execution_id(self, graph_execution_id: GraphExecutionId) -> list[GraphNodeExecution]: ...
    async def list_by_ids(self, ids: list[GraphNodeExecutionId]) -> list[GraphNodeExecution]: ...
    async def save(self, node: GraphNodeExecution) -> None: ...
    # NOWE:
    async def get_next_pending(self, graph_execution_id: GraphExecutionId) -> GraphNodeExecution | None: ...
```

> **✓ Weryfikacja etapu 2:** FSM działa (PENDING→RUNNING→COMPLETED/FAILED/TIMED_OUT). Eventy emitowane bezwarunkowo przy przejściach. `complete()` tworzy `GraphNodeExecutionStateOutput`. Testy jednostkowe przechodzą. Stare testy — mogą wymagać drobnych poprawek (mockowanie `role` zamiast `mode`).

---

## ETAP 3 — GRAPH EXECUTION (refaktor)

**Czas:** ~6h | **Zależności:** ETAP 2 | **Ryzyko:** wysokie (centralny agregat, wiele zależności)

### 3.1 Dodaj FSM

Obecnie: bezstatusowy kontener z `from_graph_definition()` i `GraphExecutionBuiltEvent`.  
Docelowo (§9):

```python
class GraphExecution(AggregateRoot[GraphExecutionId]):
    __slots__ = (
        "_task_execution_id", "_parent_graph_execution_id",
        "_depth", "_max_subgraph_depth", "_status",
        "_skills", "_state_inputs", "_state_outputs",
    )

    _task_execution_id: TaskExecutionId
    _parent_graph_execution_id: GraphExecutionId | None
    _depth: GraphDepth
    _max_subgraph_depth: MaxSubgraphDepth
    _status: GraphExecutionStatus
    _skills: list[GraphExecutionSkill]           # ETAP 3.3
    _state_inputs: list[GraphExecutionStateInput]
    _state_outputs: list[GraphExecutionStateOutput]
```

FSM (§9.2):
```
[PENDING] ──start_planning()──► [PLANNING]
                                    │
                      ┌─────────────┴─────────────┐
                      │                           │
                  spawn_subgraph()            plan_complete()
                      │                           │
                      ▼                           ▼
               [PLANNING]                    [EXECUTING]
               (utrzymane)                       │
                      │              node_completed / node_failed
                      │                           │
              sub_graph_settled()                 ▼
                      │                      [VERIFYING]
                      ▼                           │
                 [EXECUTING]          ┌───────────┴───────────┐
                                      │                       │
                                  complete()               fail()
                                      │                       │
                                 [COMPLETED]              [FAILED]
```

### 3.2 Metody i eventy

| Metoda | Przejście | Emitowany event |
|--------|-----------|-----------------|
| `start_planning()` | PENDING → PLANNING | `GraphPlanningStartedEvent` |
| `spawn_subgraph(child_id, goal)` | PLANNING → PLANNING (utrzymane) | `GraphSpawnedEvent` |
| `plan_complete(plan)` | PLANNING → EXECUTING | `GraphPlannedEvent` |
| `settle_sub_graphs(children_results)` | PLANNING → EXECUTING | `SubGraphSettledEvent` |
| `complete(verifier_result)` | VERIFYING → COMPLETED | `GraphExecutionCompletedEvent` |
| `fail(reason)` | VERIFYING → FAILED | `GraphExecutionFailedEvent` |

### 3.3 GraphExecutionSkill — encja `[NEW]`

```python
# entities/graph_execution_skill.py
@dataclass(frozen=True)
class GraphExecutionSkill:
    id: GraphExecutionSkillId         # NOWY VO
    graph_execution_id: GraphExecutionId
    payload: dict
    created_at: datetime
```

Dziedziczone z `TaskExecutionSkill` + rozszerzenia od PLANNERA (D9).

> **UWAGA:** `GraphExecutionSkillId` — dodaj do ETAPU 0.1 jako nowy ID.

### 3.4 GraphExecutionStateInput / StateOutput — z agregatów na encje `[MOV]`

Obecnie: osobne agregaty `graph_execution_state_input/` i `graph_execution_state_output/`.
Docelowo: child entities wewnątrz `GraphExecution`.

Co zrobić:
- `[MOV]` Przenieś definicje encji do `graph_execution/entities/`
- `[DEL]` Usuń osobne katalogi `graph_execution_state_input/`, `graph_execution_state_output/`
- `[MOD]` Usuń `is_current` — append-only, bez flagi
- `[DEL]` Usuń eventy `*ChangedEvent` — stan I/O nie emituje własnych eventów
- `[DEL]` Usuń puste porty repozytoriów

### 3.5 Reguła `parent_graph_execution_id` (§2.1)

| parent | znaczenie | inkrementuje current_cycle? |
|--------|-----------|---------------------------|
| `None` | Graf główny rundy | TAK |
| `<id>` | Sub-graf | NIE |

Walidacja przy tworzeniu (factory):
```python
@classmethod
def create_main_round(cls, id_, task_execution_id, depth=0, max_depth=5):
    # parent=None → runda główna
    return cls(id_, task_execution_id, None, GraphDepth(depth), MaxSubgraphDepth(max_depth), ...)

@classmethod
def create_sub_graph(cls, id_, task_execution_id, parent_id, parent_depth):
    depth = parent_depth + 1
    # parent_depth już ma max_subgraph_depth — sprawdź limit
    ...
```

### 3.6 Usunięcie dzieci z GraphExecution

Obecnie GraphExecution przechowuje:
- `_graph_node_execution_ids: list[GraphNodeExecutionId]`
- `_graph_node_execution_objects: list[Any]`
- `_transitions: list[GraphNodeTransitionExecution]`

Docelowo:
- Nody: query po `graph_execution_id` przez `GraphNodeExecutionRepository`
- Transitiony: query po `graph_execution_id` przez `GraphNodeTransitionExecutionRepository`
- Graf **NIE** trzyma kolekcji dzieci (D2, §9.1)

> **Strategia:** oznacz `@deprecated`, usuń w ETAPIE 9.

### 3.7 Aktualizacja portu repozytorium

```python
class GraphExecutionRepository(Protocol):
    async def get_by_id(self, id_: GraphExecutionId) -> GraphExecution | None: ...
    async def get_by_task_execution_id(self, task_id: TaskExecutionId) -> list[GraphExecution]: ...
    async def get_by_parent_id(self, parent_id: GraphExecutionId) -> list[GraphExecution]: ...
    async def get_main_rounds(self, task_id: TaskExecutionId) -> list[GraphExecution]: ...  # parent=None
    async def save(self, graph: GraphExecution) -> None: ...
```

> **✓ Weryfikacja etapu 3:** FSM GraphExecution przechodzi wszystkie ścieżki. `parent=None` vs `parent=<id>` rozróżniane poprawnie. `depth > max_subgraph_depth` → fail. Skill, StateInput, StateOutput encje działają jako kolekcje. `GraphSpawnedEvent` emitowany. Stare agregaty `graph_execution_state_input/output` usunięte. Testy jednostkowe.

---

## ETAP 4 — TASK EXECUTION (refaktor)

**Czas:** ~5h | **Zależności:** ETAP 3 | **Ryzyko:** wysokie (centralny agregat)

### 4.1 Dodaj FSM

Obecnie: bezstatusowy kontener (`TaskExecution.create()`).  
Docelowo (§8):

```python
class TaskExecution(AggregateRoot[TaskExecutionId]):
    __slots__ = (
        "_workflow_id", "_name", "_description",
        "_status", "_max_planning_cycles", "_current_cycle",
        "_work_dir",
        "_skills", "_state_inputs", "_state_outputs",
    )

    _workflow_id: WorkflowId
    _name: str
    _description: str
    _status: TaskExecutionStatus
    _max_planning_cycles: MaxPlanningCycles
    _current_cycle: PlanningCycle           # start=0
    _work_dir: str
    _skills: list[TaskExecutionSkill]        # frozen snapshot
    _state_inputs: list[TaskExecutionStateInput]
    _state_outputs: list[TaskExecutionStateOutput]
```

FSM (§8.2):
```
[CREATED] ──start()──► [IN_PROGRESS]
                            │
            ┌───────────────┼───────────────┐
            │               │               │
        complete()       fail()         exhaust()
            │               │               │
       [COMPLETED]      [FAILED]       [EXHAUSTED]
```

### 4.2 Metody i eventy

| Metoda | Przejście | Emitowany event |
|--------|-----------|-----------------|
| `start()` | CREATED → IN_PROGRESS | `TaskExecutionStartedEvent` |
| `complete(output)` | IN_PROGRESS → COMPLETED | `TaskExecutionCompletedEvent` |
| `fail(reason)` | IN_PROGRESS → FAILED | `TaskExecutionFailedEvent` |
| `exhaust()` | IN_PROGRESS → EXHAUSTED | `TaskExecutionExhaustedEvent` |
| `increment_cycle()` | — (nie zmienia statusu) | — |

> `increment_cycle()`: `current_cycle += 1`. Wołane przez handler `GraphExecutionCreatedEvent` dla `parent=None`. Zwraca `False` jeśli `current_cycle > max_planning_cycles` (→ handler emituje `TaskExecutionExhaustedEvent`).

### 4.3 Reguły `current_cycle` (§8.3)

- Start: **0** przy `CREATED`.
- Pierwszy graf główny → `current_cycle = 1`.
- Każdy replan → `current_cycle += 1`.
- Sub-grafy (`parent=<id>`) **NIE inkrementują**.
- `current_cycle > max_planning_cycles` → `EXHAUSTED`.

### 4.4 TaskExecutionSkill — encja `[NEW]`

```python
@dataclass(frozen=True)
class TaskExecutionSkill:
    id: TaskExecutionSkillId            # NOWY VO (dodaj do ETAPU 0.1)
    task_execution_id: TaskExecutionId
    payload: dict
    created_at: datetime
```

FREEZE w momencie tworzenia TaskExecution — kopia `SessionSkill` + `WorkflowSkill` (§7).

### 4.5 TaskExecutionStateInput / StateOutput — z agregatów na encje `[MOV]`

Analogicznie do ETAPU 3.4:
- `[MOV]` Przenieś do `task_execution/entities/`
- `[DEL]` Usuń osobne katalogi `task_execution_state_input/`, `task_execution_state_output/`
- `[MOD]` Usuń `is_current`
- `[DEL]` Usuń puste porty repozytoriów

### 4.6 Aktualizacja portu repozytorium

```python
class TaskExecutionRepository(Protocol):
    async def get_by_id(self, id_: TaskExecutionId) -> TaskExecution | None: ...
    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[TaskExecution]: ...
    async def save(self, task: TaskExecution) -> None: ...
```

> **✓ Weryfikacja etapu 4:** FSM TaskExecution. `increment_cycle()` respektuje `max_planning_cycles`. `TaskExecutionSkill` zamrażane przy `create()`. State I/O encje działają. Testy jednostkowe.

---

## ETAP 5 — WORKFLOW + SESSION (refaktor)

**Czas:** ~5h | **Zależności:** ETAP 4 (Workflow), ETAP 6 (Session — zależy od User/Project) | **Ryzyko:** średnie

> **UWAGA:** Session zależy od User/Project (ETAP 6) — referencje `user_id`, `project_id`. Ale refaktor samego Workflow może iść równolegle z ETAPEM 6. Session — po ETAPIE 6.

### 5.1 Workflow — dodaj encje skill i state

Obecnie: `id`, `session_id`, `Status`, `created_at`, `GraphNodeExecutionResult`.  
Docelowo (§6):

```python
class Workflow(AggregateRoot[WorkflowId]):
    __slots__ = (
        "_session_id", "_status", "_created_at",
        "_skills", "_state_inputs", "_state_outputs",
    )

    _session_id: SessionId
    _status: WorkflowStatus
    _created_at: datetime
    _skills: list[WorkflowSkill]
    _state_inputs: list[WorkflowStateInput]
    _state_outputs: list[WorkflowStateOutput]
```

FSM:
```
[ACTIVE] ──complete()──► [COMPLETED]
[ACTIVE] ──abort()────► [ABORTED]
```

### 5.2 WorkflowSkill — encja `[NEW]`

```python
@dataclass(frozen=True)
class WorkflowSkill:
    id: WorkflowSkillId                 # NOWY VO (dodaj do ETAPU 0.1)
    workflow_id: WorkflowId
    payload: dict
    created_at: datetime
```

Dziedziczone z Session + rozszerzenia.

### 5.3 WorkflowStateInput / StateOutput — encje `[NEW]`

Append-only. `WorkflowStateOutput` = agregat podsumowań zakończonych tasków (D8).

### 5.4 Usunięcie GraphNodeExecutionResult

`[DEL]` Usuń child entity `GraphNodeExecutionResult` z Workflow — wyniki nodów są w `GraphNodeExecutionStateOutput` (ETAP 2.3).

### 5.5 Session — refaktor

Obecnie: `goal`, `status: str` ("open"/"closed"), `opened_at`, `closed_at`.  
Docelowo (§4):

```python
class Session(AggregateRoot[SessionId]):
    __slots__ = (
        "_user_id", "_project_id",
        "_environment", "_status",
        "_opened_at", "_closed_at",
        "_skills", "_state_inputs", "_state_outputs",
    )

    _user_id: UserId                # FK → User
    _project_id: ProjectId          # FK → Project
    _environment: dict              # {os, runtime, ...}
    _status: SessionStatus
    _opened_at: datetime
    _closed_at: datetime | None
    _skills: list[SessionSkill]
    _state_inputs: list[SessionStateInput]
    _state_outputs: list[SessionStateOutput]
```

FSM:
```
[OPEN] ──close()──► [CLOSED]
```

### 5.6 SessionSkill — encja `[NEW]`

```python
@dataclass(frozen=True)
class SessionSkill:
    id: SessionSkillId                  # NOWY VO (dodaj do ETAPU 0.1)
    session_id: SessionId
    payload: dict
    created_at: datetime
```

Zamrażanie: przy `Session.open(user_id, project_id)` → kopia `UserSkill` + `ProjectSkill` → `SessionSkill` (handler, nie agregat).

### 5.7 Propagacja Stage I/O (§2.2)

Handler-y (implementacja w ETAPIE 10):

```
GraphNodeExecutionStateOutput       →  GraphExecutionStateInput    (node completed → graf)
GraphExecutionStateOutput           →  TaskExecutionStateInput     (GraphExecutionCompletedEvent)
GraphExecutionStateOutput(child)    →  GraphExecutionStateInput(parent) (SubGraphSettledEvent)
TaskExecutionStateOutput            →  WorkflowStateInput          (TaskExecutionCompletedEvent)
WorkflowStateOutput                 →  TaskExecutionStateInput     (wejście kolejnego tasku)
SessionStateOutput                  →  WorkflowStateInput          (kontekst startu)
```

> **✓ Weryfikacja etapu 5:** Workflow z nowym FSM i encjami. `GraphNodeExecutionResult` usunięty. Session z `user_id`/`project_id` (po ETAPIE 6). Testy jednostkowe.

---

## ETAP 6 — USER + PROJECT (nowe subdomeny)

**Czas:** ~4h | **Zależności:** ETAP 0 | **Ryzyko:** niskie (nowe bounded contexty, nic nie zależne)

### 6.1 Subdomena `user` — struktura `[NEW]`

```
[NEW] shell/domain/user/
  ├── __init__.py                      # re-eksportuje User, UserId, UserRepository, ...
  ├── aggregates/
  │   └── user/
  │       ├── __init__.py
  │       ├── user.py                  # AggregateRoot
  │       ├── entities/
  │       │   ├── __init__.py
  │       │   ├── user_skill.py        # UserSkill
  │       │   ├── user_state_input.py
  │       │   └── user_state_output.py
  │       ├── ports/
  │       │   ├── __init__.py
  │       │   └── user_repository.py
  │       └── exceptions/
  │           ├── __init__.py
  │           └── user_not_found.py
  ├── value_objects/
  │   ├── __init__.py
  │   ├── user_id.py                  # ETAP 0.1.6
  │   └── user_status.py              # ETAP 0.2.9
  └── ports/
      ├── __init__.py                  # ACL — porty do komunikacji z execution
      └── user_acl.py                  # UserAcl: get_user(user_id) → User
```

### 6.2 User — agregat

```python
class User(AggregateRoot[UserId]):
    __slots__ = ("_identity", "_status", "_skills", "_state_inputs", "_state_outputs")

    _identity: dict            # auth, profil
    _status: UserStatus
    _skills: list[UserSkill]
    _state_inputs: list[UserStateInput]
    _state_outputs: list[UserStateOutput]
```

FSM: `ACTIVE` ↔ `DISABLED`.  
Repozytorium: `UserRepository` — `get_by_id`, `save`.

### 6.3 Subdomena `projekt` — struktura `[NEW]`

```
[NEW] shell/domain/projekt/
  ├── __init__.py
  ├── aggregates/
  │   └── project/
  │       ├── __init__.py
  │       ├── project.py
  │       ├── entities/
  │       │   ├── __init__.py
  │       │   ├── project_skill.py
  │       │   ├── project_state_input.py
  │       │   └── project_state_output.py
  │       ├── ports/
  │       │   ├── __init__.py
  │       │   └── project_repository.py
  │       └── exceptions/
  │           ├── __init__.py
  │           └── project_not_found.py
  ├── value_objects/
  │   ├── __init__.py
  │   ├── project_id.py               # ETAP 0.1.7
  │   └── project_status.py           # ETAP 0.2.10
  └── ports/
      ├── __init__.py
      └── project_acl.py              # ProjectAcl: get_project(project_id) → Project
```

### 6.4 Project — agregat

```python
class Project(AggregateRoot[ProjectId]):
    __slots__ = ("_name", "_repo_url", "_status", "_skills", "_state_inputs", "_state_outputs")

    _name: str
    _repo_url: str | None
    _status: ProjectStatus
    _skills: list[ProjectSkill]
    _state_inputs: list[ProjectStateInput]
    _state_outputs: list[ProjectStateOutput]
```

FSM: `ACTIVE` ↔ `ARCHIVED`.

### 6.5 ACL — integracja z execution

```python
# user/ports/user_acl.py
class UserAcl(Protocol):
    async def get_user(self, user_id: UserId) -> User: ...

# projekt/ports/project_acl.py
class ProjectAcl(Protocol):
    async def get_project(self, project_id: ProjectId) -> Project: ...
```

Session używa ACL do pobrania User/Project przy `open()` → zamraża skille do `SessionSkill`.

> **✓ Weryfikacja etapu 6:** Oba agregaty kompilują się. Testy jednostkowe User i Project. ACL Protocol zdefiniowany.

---

## ETAP 7 — AGENT CONFIG EXECUTION (nowy agregat)

**Czas:** ~3h | **Zależności:** ETAP 5 (Session) | **Ryzyko:** niskie

### 7.1 Struktura `[NEW]`

```
[NEW] shell/domain/execution/aggregates/agent_config_execution/
  ├── __init__.py
  ├── agent_config_execution.py
  ├── agent_config_execution_id.py     # ETAP 0.1.2
  ├── entities/ (puste)
  ├── value_objects/
  │   ├── __init__.py
  │   └── agent_config.py              # ETAP 0.3.6
  ├── ports/
  │   ├── __init__.py
  │   └── agent_config_execution_repository.py
  └── exceptions/
      ├── __init__.py
      └── agent_config_not_found.py
```

### 7.2 AgentConfigExecution — agregat

```python
class AgentConfigExecution(AggregateRoot[AgentConfigExecutionId]):
    __slots__ = ("_session_id", "_config", "_created_at", "_updated_at")

    _session_id: SessionId
    _config: AgentConfig
    _created_at: datetime
    _updated_at: datetime
```

- UNIQUE na `session_id` (max 1 rekord na sesję).
- Nie append-only — UPDATE `config` w miejscu.
- Źródło configu dla PLANNER i AGENT.
- Brak rekordu → config domyślny z kodu.

### 7.3 Repozytorium

```python
class AgentConfigExecutionRepository(Protocol):
    async def get_by_id(self, id_: AgentConfigExecutionId) -> AgentConfigExecution | None: ...
    async def get_by_session_id(self, session_id: SessionId) -> AgentConfigExecution | None: ...
    async def save(self, config: AgentConfigExecution) -> None: ...
```

> **✓ Weryfikacja etapu 7:** Agregat kompiluje się. `get_by_session_id` zwraca None lub konfig. Testy jednostkowe.

---

## ETAP 8 — SCHEDULER (nowa subdomena + przepisanie)

**Czas:** ~8h | **Zależności:** ETAP 4, 5, 7 | **Ryzyko:** wysokie (przepisanie serca systemu)

### 8.1 Subdomena `scheduling` — refaktor struktury

Obecny scheduler jest rozproszony: część w `domain/scheduling/`, część w handlerach.  
Docelowo: scheduler jako **osobna subdomena**, wywoływana z frameworka (CLI/FastAPI).

```
[MOD] shell/domain/scheduling/
  ├── __init__.py
  ├── aggregates/
  │   ├── scheduler_definition.py         # [ISTNIEJE] — zostaje
  │   ├── scheduler_execution.py          # [ISTNIEJE] — zostaje
  │   └── scheduler_job.py                # [ISTNIEJE] — zostaje
  ├── services/
  │   ├── scheduler_orchestrator.py       # [ISTNIEJE] — do refaktoru
  │   └── [NEW] dual_layer_dispatcher.py  # NOWY: dispatcher dwuwarstwowy
  ├── ports/
  │   ├── graph_execution_launcher.py     # [ISTNIEJE] — do refaktoru
  │   └── [NEW] pending_graph_finder.py   # NOWY: wyszukiwanie PENDING grafów
  └── value_objects/ (istniejące)
```

### 8.2 Dual-layer dispatcher (§14, D3) `[NEW]`

```python
class DualLayerDispatcher:
    """Dispatch eventów w dwóch warstwach:
    1. Komunikacyjne (*Execution*Event) — zawsze pierwsze
    2. Decyzyjne (*Transition*Event) — gdy inbox komunikacyjny pusty
    """

    async def dispatch_loop(self, inbox: Inbox, outbox: Outbox, handlers: HandlerRegistry):
        while True:
            # Warstwa 1: komunikacyjne
            while (event := inbox.pop_communication_event()) is not None:
                await handlers.dispatch(event)  # → zmiany stanu, nowe eventy → outbox

            # Przepisz outbox → inbox
            outbox.flush_to(inbox)

            # Warstwa 2: decyzyjne (tylko gdy komunikacyjne puste)
            if inbox.communication_is_empty():
                while (event := inbox.pop_decision_event()) is not None:
                    await handlers.dispatch(event)
                outbox.flush_to(inbox)

            # Gdy obie puste → szukaj PENDING grafów
            if inbox.is_empty() and outbox.is_empty():
                await self._lift_pending_graphs()
                if outbox.is_empty():
                    break  # nic więcej do zrobienia w tej iteracji
```

### 8.3 Pending graph finder (§14 krok 4) `[NEW]`

```python
class PendingGraphFinder:
    """Znajduje grafy gotowe do startu."""

    async def find_next(self, repo: GraphExecutionRepository) -> GraphExecution | None:
        """Kryteria (wszystkie muszą być spełnione):
        a) GraphExecution.status == PENDING
        b) parent_graph_execution_id IS NULL LUB parent.status == PLANNING
        c) TaskExecution.status == IN_PROGRESS
        d) current_cycle <= max_planning_cycles
        """
```

### 8.4 SubGraphSettledEvent — emission logic

Gdy handler `GraphExecutionCompletedEvent`/`GraphExecutionFailedEvent` przetwarza child graph:
1. Znajdź parenta przez `parent_graph_execution_id`
2. Query: `get_by_parent_id(parent_id)` → wszystkie dzieci
3. Jeśli **wszystkie** dzieci w stanie końcowym (COMPLETED/FAILED) → emituj `SubGraphSettledEvent`
4. `SubGraphSettledEvent` handler: absorbuj `children_results` do `GraphExecutionStateInput` parenta, resume PLANNER

> **CrownScheduler NIE jest potrzebny** — jego logika (query po dzieciach, sprawdzenie statusów) jest wbudowana w handler emitujący `SubGraphSettledEvent`. Scheduler jako subdomena sam orkiestruje.

### 8.5 Usunięcie CrownScheduler `[DEL]`

- `[DEL]` `shell/domain/execution/aggregates/graph_execution/ports/crown_scheduler.py` — Protocol
- `[DEL]` `shell/infrastructure/execution/orchestration/in_memory_crown_scheduler.py` — implementacja
- `[DEL]` `shell/domain/execution/ports/__init__.py` — re-eksport CrownScheduler
- `[DEL]` `shell/tests/execution/unit/domain/test_crown_scheduler.py` — testy
- `[MOD]` `shell/bootstrap/.../infrastructure_container.py` — usuń `QueryBasedCrownScheduler` z DI

> **✓ Weryfikacja etapu 8:** Dual-layer dispatcher nie przetwarza decyzyjnych przed komunikacyjnymi. PendingGraphFinder zwraca tylko spełniające kryteria. SubGraphSettledEvent emitowany dopiero po ostatnim dziecku. Testy integracyjne: cały flow PENDING→PLANNING→EXECUTING→VERIFYING→COMPLETED.

---

## ETAP 9 — CZYSTKI

**Czas:** ~3h | **Zależności:** ETAP 1-8 zakończone | **Ryzyko:** niskie

### 9.1 Usunięcie PARALLEL/JOIN (D6)

- `[MOD]` `TransitionType` — już usunięte w ETAPIE 0.4.1
- `[DEL]` Wszelkie handler-y odnoszące się do `parallel`/`join`
- `[DEL]` `GraphNodeParallelExecutionRequestedEvent`

### 9.2 Usunięcie orphan eventów

Eventy, które nie są już emitowane przez żaden agregat:

| Plik `[DEL]` | Dawny emiter |
|--------------|-------------|
| `graph_execution/events/graph_execution_built_event.py` | `GraphExecution.from_graph_definition()` |
| `graph_execution/events/child_graph_completed_event.py` | handler (zastąpiony SubGraphSettledEvent) |
| `graph_execution/events/sub_graph_execution_started_event.py` | handler |
| `graph_execution/events/sub_graph_spawn_requested_event.py` | handler |
| `graph_node_execution/events/planner_result_event.py` | `GraphNodeExecution.record_planner_result()` |
| `graph_node_execution/events/planner_spawns_queued_event.py` | handler |
| `graph_node_execution/events/graph_node_execution_condition_evaluated_event.py` | handler → TransitionConditionEvaluatedEvent |
| `graph_node_execution/events/graph_node_execution_loop_iteration_event.py` | handler → TransitionLoopedEvent |
| `graph_node_execution/events/graph_node_execution_timed_out_event.py` | handler → TransitionTimedOutEvent |
| `graph_node_execution/events/graph_node_parallel_execution_requested_event.py` | handler |

### 9.3 Usunięcie starych agregatów state I/O

- `[DEL]` `shell/domain/execution/aggregates/task_execution_state_input/` (przeniesione do TaskExecution)
- `[DEL]` `shell/domain/execution/aggregates/task_execution_state_output/` (jw.)
- `[DEL]` `shell/domain/execution/aggregates/graph_execution_state_input/` (przeniesione do GraphExecution)
- `[DEL]` `shell/domain/execution/aggregates/graph_execution_state_output/` (jw.)

### 9.4 Usunięcie `GraphNodeExecutionResult`

- `[DEL]` `workflow/entities/graph_node_execution_result.py` (wyniki → GraphNodeExecutionStateOutput)
- `[MOD]` Workflow — usuń referencje do `GraphNodeExecutionResult`

### 9.5 Usunięcie starych pól z agregatów

| Agregat | Do usunięcia | Zastąpione przez |
|---------|-------------|-----------------|
| `GraphNodeExecution` | `mode`, `node_type`, `command`, `timeout`, `retries`, `log_level`, `max_step`, `no_ask_user`, `autopilot`, `task_execution_id`, `source_dir`, `status_initial`, `timeout_seconds`, `max_retries`, `retry_delay_seconds`, `model` | `role: NodeRole`, `order: NodeOrder`, `status: GraphNodeExecutionStatus` |
| `GraphExecution` | `_graph_node_execution_ids`, `_graph_node_execution_objects`, `_transitions` | query przez repozytoria nodów i transitionów |
| `Workflow` | `_status` (stary Status) | `_status` (WorkflowStatus) |

### 9.6 Usunięcie deprecated VO

- `[DEL]` `Status` z `platform/value_objects/status.py` — zastąpiony dedykowanymi
- `[DEL]` `Mode` z `platform/value_objects/mode.py` — zastąpiony `NodeRole`

### 9.7 Wyczyść TODO V2

- `[MOD]` `shell/application/execution/event_handlers/graph_node_execution_requested_handler.py` — usuń komentarze TODO V2
- `[MOD]` `shell/application/execution/event_handlers/graph_node_execution_worker.py` — usuń TODO V2
- `[MOD]` `shell/application/execution/event_handlers/graph_node_execution_timed_out_handler.py` — usuń TODO V2
- `[MOD]` `shell/application/execution/command_handlers/run_graph_node_execution_handler.py` — usuń TODO V2
- `[MOD]` `shell/tests/definition/conftest.py` — usuń `# TODO V2: WorkflowExecutionContext removed`
- `[MOD]` `shell/tests/execution/conftest.py` — jw.
- `[MOD]` `shell/tests/platform/conftest.py` — jw.

> **✓ Weryfikacja etapu 9:** `rg "V2" shell/domain/ shell/application/ shell/tests/` — zero wyników. `rg "Parallel|PARALLEL" shell/domain/` — zero wyników. Wszystkie testy przechodzą.

---

## INFRASTRUKTURA (równolegle z ETAPAMI 1-9)

Dla każdego nowego/zmienionego agregatu — invariant "6 miejsc" (antywzorzec #1):

### Na każdy agregat (`[NEW]` lub `[MOD]`):

| Krok | Co | Gdzie |
|------|-----|-------|
| I1 | ORM Model (SQLAlchemy) | `shell/infrastructure/execution/persistence/models/` |
| I2 | Migracja Alembic | `shell/infrastructure/.../migrations/sql/versions/` |
| I3 | SQL Repository (implementacja portu) | `shell/infrastructure/execution/persistence/repositories/` |
| I4 | InMemory Repository (pełna semantyka) | `shell/infrastructure/execution/persistence/in_memory/` |
| I5 | DTO + Mapper | `shell/application/execution/dto/` + `mappers/` |
| I6 | DI Container + Factory rejestracja | `shell/bootstrap/platform/container/` |

### Kolejność dla każdego agregatu:

1. Domain (ETAP 1-7) — agregat, porty, VO, eventy
2. ORM Model + migracja (I1, I2)
3. SQL Repository (I3)
4. InMemory Repository (I4)
5. DTO + Mapper (I5)
6. DI rejestracja (I6)
7. Testy jednostkowe (domain)
8. Testy integracyjne (SQLite)

---

## HANDLERY (równolegle z ETAPAMI 2-8)

### Handler-y do implementacji — per event:

#### TaskExecution (§13.1)

| Event | Handler | Co robi |
|-------|---------|---------|
| `TaskExecutionCreatedEvent` | Istnieje — zachować | Tworzy pierwszy `GraphExecution` (`parent=None`); inkrementuje `current_cycle` |
| `TaskExecutionStartedEvent` | `[NEW]` | `TaskExecution.status → IN_PROGRESS` |
| `TaskExecutionCompletedEvent` | `[NEW]` | Output → `WorkflowStateInput` (propagacja §2.2) |
| `TaskExecutionFailedEvent` | `[NEW]` | `TaskExecution.status → FAILED` |
| `TaskExecutionExhaustedEvent` | `[NEW]` | `TaskExecution.status → EXHAUSTED` |

#### GraphExecution (§13.2)

| Event | Handler | Co robi |
|-------|---------|---------|
| `GraphExecutionCreatedEvent` | `[NEW]` | Jeśli `parent=None`: `TaskExecution.increment_cycle()`. Jeśli `depth > max_subgraph_depth` → `GraphExecutionFailedEvent`. Goal → `GraphExecutionStateInput` |
| `GraphPlanningStartedEvent` | `[NEW]` | Uruchom PLANNER node |
| `GraphSpawnedEvent` | `[NEW]` | Tworzy child `GraphExecution` z `parent=parent_id` |
| `GraphPlannedEvent` | `[NEW]` | Plan → `GraphExecutionStateInput`, uruchom pierwszy node |
| `SubGraphSettledEvent` | `[NEW]` | Absorbuj `children_results` → `GraphExecutionStateInput` parenta, resume PLANNER |
| `GraphExecutionCompletedEvent` | `[NEW]` | Jeśli `parent=None` → `TaskExecutionCompletedEvent`. Jeśli `parent=X` → sprawdź settled + `SubGraphSettledEvent` |
| `GraphExecutionFailedEvent` | `[NEW]` | Jeśli `parent=None`: replan (nowy graf) LUB `TaskExecutionExhaustedEvent`. Jeśli `parent=X` → fail bubluje przez `SubGraphSettledEvent` |

#### Replan handler (§16)

```python
# GraphExecutionFailedEvent handler dla parent=None:
next_cycle = task.current_cycle + 1
if next_cycle > task.max_planning_cycles:
    emit TaskExecutionExhaustedEvent
else:
    emit GraphExecutionCreatedEvent(
        task_execution_id=task.id,
        parent_graph_execution_id=None,
        goal="replan: " + failed_graph.description,
        state_input={"previous_attempt_id": failed_graph.id}
    )
```

#### GraphNodeExecution (§13.3)

| Event | Handler | Co robi |
|-------|---------|---------|
| `GraphNodeExecutionStartedEvent` | `[NEW]` | Jeśli `role=AGENT` → utwórz `AgentExecution` z configiem i skilami |
| `GraphNodeExecutionCompletedEvent` | `[NEW]` | Result → `GraphNodeExecutionStateOutput`. Jeśli `role=VERIFIER` → `GraphExecutionCompletedEvent`/`FailedEvent`. Edge → ewaluuj outgoing transitions |
| `GraphNodeExecutionFailedEvent` | `[NEW]` | Jeśli `role=VERIFIER` → `GraphExecutionFailedEvent`. Jeśli `role=PLANNER` → `GraphExecutionFailedEvent`. Jeśli `AGENT/TOOLS` → Edge `ERROR_HANDLER` LUB VERIFIER z błędem |

#### Skill freeze handler-y

| Event | Handler | Co robi |
|-------|---------|---------|
| `SessionOpenedEvent` | `[NEW]` | Kopiuj `UserSkill` + `ProjectSkill` → `SessionSkill` |
| `TaskExecutionCreatedEvent` (rozszerzenie) | `[MOD]` | Kopiuj `SessionSkill` + `WorkflowSkill` → `TaskExecutionSkill` (freeze) |

---

## TESTY

### Dla każdego etapu:

| Poziom | Co testować |
|--------|------------|
| **Unit (domain)** | FSM — każde przejście, każdy wyjątek. Eventy emitowane bezwarunkowo. Walidacja VO. |
| **Unit (application)** | Handlery — mockowane repo, weryfikacja eventów w outboxie. |
| **Integration** | SQLite — full roundtrip: agregat → repo.save → repo.get_by_id → porównanie pól. |
| **E2E** | Cały flow: TaskExecutionCreated → GraphExecution PENDING → PLANNER → AGENT → VERIFIER → COMPLETED. |

---

## CHECKLISTA GLOBALNA (końcowa)

- [ ] Wszystkie agregaty z §1 DOMAINV3.md istnieją: User, Project, Session, AgentConfigExecution, Workflow, TaskExecution, GraphExecution, GraphNodeExecution, GraphNodeTransitionExecution, AgentExecution
- [ ] Wszystkie encje skili istnieją: `UserSkill`, `ProjectSkill`, `SessionSkill`, `WorkflowSkill`, `TaskExecutionSkill`, `GraphExecutionSkill`, `AgentSkillExecution`
- [ ] Wszystkie encje State I/O istnieją (append-only, bez `is_current`, per agregat): `*StateInput`, `*StateOutput` dla User, Project, Session, Workflow, TaskExecution, GraphExecution, GraphNodeExecution
- [ ] Każdy agregat ma dedykowany status (nie uniwersalny `Status`)
- [ ] Wszystkie eventy z §13 istnieją i są emitowane z właściwych agregatów
- [ ] Dual-layer dispatcher w schedulerze (D3)
- [ ] PendingGraphFinder (D6 — tylko SEQUENCE, brak PARALLEL/JOIN)
- [ ] `parent_graph_execution_id` reguła (§2.1) — inkrementacja tylko dla `parent=None`
- [ ] `max_subgraph_depth` + `depth` z walidacją (D5)
- [ ] Propagacja Stage I/O (§2.2) przez handlery
- [ ] Skill freeze: User/Project → Session, Session+Workflow → TaskExecution (§7)
- [ ] Replan: nowy GraphExecution z `parent=None`, brak flagi "replanowalności" (§16)
- [ ] Subdomena `user/` z ACL
- [ ] Subdomena `projekt/` z ACL
- [ ] `CrownScheduler` usunięty
- [ ] `GraphNodeExecutionResult` usunięty
- [ ] Stare agregaty state I/O usunięte
- [ ] PARALLEL/JOIN usunięte
- [ ] Wszystkie stare TODO V2 usunięte
- [ ] `mypy --strict` przechodzi
- [ ] Wszystkie testy przechodzą
- [ ] Żadnego `# noqa` ani `type: ignore[...]` bez uzasadnienia
