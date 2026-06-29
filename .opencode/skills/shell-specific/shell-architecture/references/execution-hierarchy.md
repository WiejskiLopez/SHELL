# Execution Hierarchy

Czteropoziomowa hierarchia wykonawcza SHELL: Workflow → GraphExecution → GraphNodeExecution → Sub-graf.

## Diagram

```
Workflow (koordynuje N GraphExecution)
  └── GraphExecution (instancja grafu)
        ├── GraphNodeExecution: AGENT / TOOL / WORKER
        ├── GraphNodeExecution: PLANNER
        │     └── child: GraphExecution (sub-graf, depth+1)
        │           ├── GraphNodeExecution: ...
        │           └── ...
        └── GraphNodeExecution: TASKER (spawnuje sub-graf)
              └── child: GraphExecution
                    └── ...
```

## Poziomy

| Poziom | Klasa | Lokalizacja | Opis | Relacja |
|--------|-------|-------------|------|---------|
| **Workflow** | `Workflow` (aggregate) | `domain/execution/aggregates/workflow/` | Koordynuje sekwencję node'ów, trzyma cursor (`WorkflowCursor`), stany `GraphNodeExecutionState` i wyniki `GraphNodeExecutionResult` | 1 → N GraphExecution |
| **GraphExecution** | `GraphExecution` (aggregate) | `domain/execution/aggregates/graph_execution/` | Materializacja definicji grafu; własne `GraphNodeExecution`, transitiony, loop counters; może być sub-grafem (ma `_parent_graph_execution_id`) | 1 → N GraphNodeExecution, 0 → N child GraphExecution |
| **GraphNodeExecution** | `GraphNodeExecution` (entity) | `domain/execution/entities/` | Pojedynczy krok wykonawczy — AGENT, TOOL, WORKER, PLANNER, ROUTER, TASKER | należy do GraphExecution |
| **Sub-graf** | `GraphExecution` z `_parent_graph_execution_id` | jw. | Dziecięcy graf spawnowany przez PLANNER lub TASKER node | depth = parent.depth + 1 |

## Kluczowe relacje (DDD)

| FK | Na encji (pole) | Typ | Cel |
|----|-----------------|-----|-----|
| `_workflow_id` | `TaskExecution`, `GraphExecution` | `WorkflowId \| None` | Task/Graph → Workflow |
| `_task_execution_id` | `GraphExecution` | `TaskExecutionId` | Graph → Task |
| `_parent_graph_execution_id` | `GraphExecution` | `GraphExecutionId \| None` | Self-referencing FK — sub-graf → parent graph |
| `_parent_tasker_node_execution_id` | `GraphExecution` | `GraphNodeExecutionId \| None` | Który TASKER node w parent go stworzył |
| `_workflow_id` | `GraphExecution` | `WorkflowId` | Denormalizacja dla szybkich lookupów (unika antywzorca #3) |

## Agregaty domeny execution

| Agregat | Kluczowe pola | Odpowiedzialność |
|---------|--------------|------------------|
| `Workflow` | `_status`, `_cursor`, `_execution_context`, `_graph_node_execution_states`, `_graph_node_execution_results` | Orkiestracja sekwencji node'ów; `advance_to()`, `wait_for_children()`, `finish()`, `abort()` |
| `GraphExecution` | `_graph_node_executions`, `_transitions`, `_loop_counters`, `_parent_graph_execution_id`, `_depth`, `_state_input`, `_state_output`, `_correlation_id`, `_tags`, `_timeout_at` | Runtime snapshot grafu; budowany przez `from_graph_definition()` |
| `GraphExecutionState` | `_state_data`, `_is_current` | Współdzielony stan key-value dla grafu (osobny agregat, inna granica transakcyjna) |
| `TaskExecution` | `_name`, `_version`, `_hash`, `_body`, `_work_dir`, `_workflow_id`, `_parent_task_execution_id` | Wersjonowana jednostka pracy |

## Mody węzłów (Mode enum)

`Mode` w `domain/platform/value_objects/mode.py`:

| Wartość | Przeznaczenie | Strategia wykonawcza |
|---------|---------------|---------------------|
| `AGENT` | Wykonuje agenta (LLM subprocess) | `AgentStrategy` |
| `TOOL` | Wykonuje narzędzie (funkcja) | `ToolStrategy` |
| `WORKER` | Worker mode | `WorkerStrategy` |
| `ROUTER` | Routing warunkowy | `RouterStrategy` |
| `PLANNER` | LLM planuje kroki; po zakończeniu `SpawnSubGraphsOnPlannerCompletionHandler` parsuje output | `PlannerStrategy` |
| `TASKER` | "Foreign function call" do sub-grafu; `SubGraphExecutionService.spawn()` | `TaskerStrategy` |

## GraphExecution — kluczowe metody

### `from_graph_definition()` (factory)

Buduje `GraphExecution` z `GraphExecutionDefinition` (runtime snapshot definicji):
- Tworzy `GraphNodeExecution` dla każdego `GraphNodeExecutionDefinition`
- Tworzy `GraphNodeTransitionExecution` dla każdej transition
- Inicjalizuje `LoopCounter` dla pętli
- Ustawia `_graph_definition_id`, `_task_execution_id`, `_workflow_id`
- Jeśli sub-graf: ustawia `_parent_graph_execution_id`, `_depth`, `_state_input`, `_correlation_id`, `_tags`
- Emituje `GraphExecutionBuiltEvent`

### Metody zarządzania sub-grafami

- `absorb_child_results(combined_output)` — merge `state_output` dzieci do stanu rodzica
- Właściwości: `parent_graph_execution_id`, `depth`, `correlation_id`, `tags`, `state_input`, `state_output`

## GraphNodeExecution — kluczowe pola sub-grafu

| Pole | Typ | Opis |
|------|-----|------|
| `_sub_graph_definition_id` | `str \| None` | FK → `GraphDefinition` (definicja pod-grafu) |
| `_sub_graph_definition_version` | `int \| None` | Wersja definicji do użycia (snapshot versioning) |
| `_timeout_seconds` | `int` | Timeout na wykonanie tego noda (override definicji) |
| `_max_retries` | `int` | Maksymalna liczba retry |
| `_retry_delay_seconds` | `int` | Opóźnienie między retry |
