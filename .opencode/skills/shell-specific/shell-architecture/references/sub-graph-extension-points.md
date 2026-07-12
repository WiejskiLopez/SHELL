# Sub-graph Flows & Extension Points

Sub-graf to `GraphExecution` z ustawionym `_parent_graph_execution_id`. Spawnują go PLANNER lub TASKER node'y.

## PLANNER node

`Mode.PLANNER` — LLM generuje plan kolejnych kroków. Po zakończeniu wykonania noda:

1. `SpawnSubGraphsOnPlannerCompletionHandler` parsuje JSON output planera
2. Dla każdego kroku z `action="spawn_sub_graph"` woła `SubGraphExecutionService.spawn()`
3. `CrownScheduler.register_child(parent, child)` rejestruje dziecko
4. `Workflow.wait_for_children()` → workflow status `waiting`
5. Po zakończeniu wszystkich dzieci → `NotifyParentOnChildCompletionHandler` → parent kontynuuje

### Planner JSON output format

```json
{
  "steps": [
    {
      "action": "spawn_sub_graph",
      "sub_graph_definition_id": "gd_analysis",
      "reason": "Potrzebna analiza danych",
      "state_input": {"key": "value"}
    }
  ]
}
```

## TASKER node

`Mode.TASKER` + `sub_graph_definition_id` — "foreign function call" do sub-grafu.
Nie spawnuje procesu, spawnuje inny `GraphExecution`.

1. `NodeExecutionWorker` wykrywa `mode=TASKER` + `sub_graph_definition_id`
2. Deleguje do `SubGraphExecutionService.spawn()` (zamiast subprocessu)
3. TASKER zostaje `IN_PROGRESS` — workflow cursor nie rusza
4. Sub-graf wykonuje się niezależnie (może mieć własne TASKERY, PLANERY, etc.)
5. Po zakończeniu sub-grafu → `NotifyParentOnChildCompletionHandler` → TASKER → `SUCCESS` → normalny advance

## Sub-graf — przepływ kompletny

```
GraphExecution (parent, depth=D)
  └── TASKER node
        └── SubGraphExecutionService.spawn()
              ├── Governance: can_spawn(parent, def_id, depth+1)?
              ├── Security: resolve_scope + filter_state(parent_state)
              ├── Versioning: resolve_definition(def_id, version, parent)
              ├── Tworzy GraphExecution (depth+1, parent_graph_execution_id=parent.id)
              ├── Observer: on_start(ctx)
              └── Uruchamia execution (pierwszy node child grafu)

GraphExecution (child, depth=D+1) ... → koniec

  └── NotifyParentOnChildCompletionHandler
        ├── CrownScheduler.on_child_completed(child_id)
        ├── Merge child state_output → TASKER.output_payload
        ├── Oznacza TASKER jako SUCCESS
        └── workflow.record_node_execution_result(TASKER, SUCCESS)
              └── NodeExecutionCompletedEvent → normalny Cycle B advance
```

## SubGraphExecutionService.spawn()

`SubGraphExecutionService` w `domain/execution/aggregates/graph_execution/services/sub_graph_execution_service.py`.
Domain service — wszystkie operacje w jednej jednostce pracy.

```python
async def spawn(
    self,
    *,
    parent_graph: GraphExecution,
    tasker_node: NodeExecution,
    sub_graph_definition_id: str,
    version: int | None = None,
    state_input: dict | None = None,
) -> GraphExecution: ...
```

### Krok po kroku

1. **Governance**: `await self._governance.can_spawn(parent_graph, definition_id, depth+1)`
   - Jeśli nie → rzuca `SubGraphSpawnDenied`
2. **Versioning**: `await self._versioning.resolve_definition(definition_id, version, parent_graph)`
   - Zwraca `GraphDefinition` (może być pinned, latest lub snapshot)
3. **Security**: `await self._security.resolve_scope(parent_graph, sub_graph)`
   - Określa Scope: FULL, FILTERED, ISOLATED
4. **Security**: `await self._security.filter_state(parent_state, sub_graph)`
   - Filtruje stan rodzica zgodnie z scope
5. **Stworzenie child GraphExecution**:
   - `GraphExecution.from_graph_definition()` z ustawionym `_parent_graph_execution_id`, `_depth`, `_state_input`, `_correlation_id`, `_tags`
   - Uruchomienie execution (pierwszy node)
6. **Observer**: `await self._observer.on_start(ctx)`
7. **Rejestracja CrownScheduler**: `self._crown_scheduler.register_child(parent_graph.id, child.id)`
8. **Workflow**: `parent_graph.workflow.wait_for_children()` → status `waiting`

## CrownScheduler

Port (`Protocol`) w `domain/execution/ports/crown_scheduler.py` — orkiestruje parent-child lifecycle.

```python
class CrownScheduler(Protocol):
    async def register_child(
        self, parent_graph_execution_id: GraphExecutionId, child_graph_execution_id: GraphExecutionId
    ) -> None: ...

    async def on_child_completed(self, child_graph_execution_id: GraphExecutionId) -> None: ...

    async def on_child_failed(self, child_graph_execution_id: GraphExecutionId) -> None: ...
```

- `register_child()` — zapisuje relację parent-child
- `on_child_completed()` — sprawdza czy wszystkie dzieci skończyły; jeśli tak → notify parent
- `on_child_failed()` — podobnie, ale dla failure case

## Extension points (Protocols)

| Port (Protocol) | Lokalizacja | Domyślna implementacja | Metody |
|----------------|-------------|------------------------|--------|
| `SubGraphGovernance` | `domain/execution/ports/sub_graph_governance.py` | `PermissiveGovernance` | `can_spawn()`, `max_parallel_sub_graphs()`, `max_depth()`, `token_budget()` |
| `SubGraphSecurity` | `domain/execution/ports/sub_graph_security.py` | `FullAccessSecurity` | `resolve_scope()`, `filter_state()` |
| `SubGraphVersioning` | `domain/execution/ports/sub_graph_versioning.py` | `LatestVersionStrategy` | `resolve_definition()` |
| `SubGraphObserver` | `domain/execution/ports/sub_graph_observer.py` | `LoggingObserver` | `on_start()`, `on_complete()`, `on_fail()`, `on_timeout()` |
| `SubGraphCompensation` | `domain/execution/ports/sub_graph_compensation.py` | `NoOpCompensation` | `compensate()`, `on_child_failed()` |
| `SubGraphPolicy` | `domain/execution/ports/sub_graph_policy.py` | `RetryPolicy` | `on_timeout()`, `on_failure()`, `on_depth_exceeded()` |

### Governance

```python
class SubGraphGovernance(Protocol):
    async def can_spawn(self, parent: GraphExecution, definition_id: str, depth: int) -> bool: ...
    async def max_parallel_sub_graphs(self, graph_execution: GraphExecution) -> int: ...
    async def max_depth(self, root_graph_execution: GraphExecution) -> int: ...
    async def token_budget(self, graph_execution: GraphExecution) -> TokenBudget | None: ...
```

Implementacje: `ConfigBasedGovernance` (limity z configu), `LLMGovernance` (LLM decyduje), `TenantAwareGovernance`.

### Policy (resilience)

```python
class SubGraphPolicy(Protocol):
    async def on_timeout(self, graph_execution: GraphExecution, node: NodeExecution) -> Decision: ...
    async def on_failure(self, graph_execution: GraphExecution, node: NodeExecution, reason: str) -> Decision: ...
    async def on_depth_exceeded(self, graph_execution: GraphExecution, max_depth: int) -> Decision: ...
```

`Decision.action`: `"retry"`, `"abort"`, `"compensate"`, `"skip"`, `"fallback"`.

Mechanizmy out-of-the-box: retry z backoffem, timeout na sub-graf, circuit breaker, dead letter queue.

### Observer

```python
class SubGraphObserver(Protocol):
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
    duration_ms: float | None
```

Built-in: audit event na każdą zmianę stanu. Extension: OpenTelemetry, Prometheus, structured logging.

### Compensation

```python
class SubGraphCompensation(Protocol):
    async def compensate(self, graph_execution: GraphExecution, reason: str) -> None: ...
    async def on_child_failed(self, parent_graph: GraphExecution, child_graph: GraphExecution, tasker_node: NodeExecution) -> CompensationDecision: ...
```

Strategie: `NoOpCompensation` (brak cofania), `RollbackStateCompensation` (przywraca stan sprzed sub-grafu), `SagaCompensation` (cofa każdy węzeł od tyłu).

### Versioning

```python
class SubGraphVersioning(Protocol):
    async def resolve_definition(self, definition_id: str, version: int | None, parent: GraphExecution) -> GraphDefinition: ...
```

Strategie: `PinVersionStrategy` (konkretna wersja), `LatestVersionStrategy` (najnowsza), `SnapshotStrategy` (full freeze w `extra`).

Rozwiązywane tylko raz — w momencie spawnu. `GraphExecution` jest zamrożony; zmiana `GraphDefinition` nie wpływa na działające execution.

## Kluczowe reguły sub-grafów

1. **Brak SUSPENDED** — parent czeka bo cursor nie rusza; tasker node `IN_PROGRESS` dopóki sub-graf nie skończy
2. **Brak child task_execution** — sub-graf to osobny `GraphExecution`, nie osobny `TaskExecution`
3. **Stan przekazywany explicit** — parent → `state_input` → child → `state_output` → `TaskerNode.output_payload`
4. **Równoległość przez PARALLEL+JOIN** — sub-grafy równolegle korzystają z `ParallelGroup` i `JoinCounter` (zero nowej logiki)
5. **Snapshot versioning** — `GraphExecution` zamrożony po spawnie; zmiana `GraphDefinition` nie wpływa na działające execution
6. **Wszystko przez `extra`** — rozszerzenia danych przez JSONB `extra` na encjach; zero migracji dla nowych pól
7. **Extension points = Protocols** — każda warstwa enterprise to interfejs; brak implementacji = brak warstwy

## Eventy sub-grafów

| Event | Kiedy emitowany | Handler |
|-------|----------------|---------|
| `SubGraphExecutionStartedEvent` | Po spawnie sub-grafu | — |
| `GraphExecutionCompletedEvent` | Sub-graf skończony | `NotifyParentOnChildCompletionHandler` |
| `GraphExecutionFailedEvent` | Sub-graf failed | `NotifyParentOnChildCompletionHandler` |
| `ChildGraphsCompletedEvent` | Wszystkie dzieci skończone | — |
