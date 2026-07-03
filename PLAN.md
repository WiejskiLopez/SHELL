# Plan: GraphNodeLinkDefinition + GraphNodeLinkExecution

## Cel

Zastąpienie bezpośrednich relacji FK między agregatami parami link-table (wzorzec wielu-do-wielu przez osobny agregat):

| Obecnie (do usunięcia) | Nowy agregat |
|---|---|
| `GraphNodeDefinition.graph_definition_id` FK | `GraphNodeLinkDefinition` |
| `GraphDefinition._graph_node_definition_ids` lista ID | `GraphNodeLinkDefinition` |
| `GraphNodeExecution.graph_execution_id` FK | `GraphNodeLinkExecution` |
| `GraphExecution._graph_node_definition_execution_slots` JSONB | `GraphNodeLinkExecution` |

## Przepływ danych (Execution)

```
1. Event/komenda → tworzy GraphExecution (bez slotów, bez node_executions)
   → emituje GraphExecutionCreatedEvent (tylko graph_execution_id + graph_definition_id)

2. Saga odbiera event → przez provider wyszukuje GraphNodeDefinitionIds
   powiązane z GraphDefinition (przez GraphNodeLinkDefinition)
   → dla każdego emituje CreateGraphNodeExecutionCommand

3. CreateGraphNodeExecutionCommand → tworzy GraphNodeExecution (bez FK do execution)
   → emituje GraphNodeExecutionCreatedEvent (graph_execution_id, graph_node_execution_id)

4. GraphNodeLinkExecutionHandler odbiera event → tworzy GraphNodeLinkExecution
   (łączy GraphExecution + GraphNodeExecution)
   → emituje GraphNodeLinkExecutionCreatedEvent

5. Saga odbiera GraphNodeLinkExecutionCreatedEvent → wie że node jest gotowy
   → gdy wszystkie linki utworzone → kończy sagę, emituje GraphExecutionReadyEvent
```

## Kolejność implementacji

### Faza 1: Definition BC – GraphNodeLinkDefinition

1. VO: `GraphNodeLinkDefinitionId` w `shell/domain/definition/aggregates/graph_node_link_definition/value_objects/`
2. Agregat: `GraphNodeLinkDefinition` w `shell/domain/definition/aggregates/graph_node_link_definition/`
3. Event: `GraphNodeLinkDefinitionCreatedEvent`
4. Port repozytorium: `GraphNodeLinkDefinitionRepository`
5. Model SQL: `GraphNodeLinkDefinitionModel`
6. Repozytorium SQL: `SqlGraphNodeLinkDefinitionRepository`
7. Repozytorium InMemory: `InMemoryGraphNodeLinkDefinitionRepository`
8. Mapper: w `shell/infrastructure/definition/persistence/sql/mappers/`
9. Migracja: tworzy tabelę `graph_node_link_definition`
10. Seed data: migracja dodająca linki dla istniejących GraphDefinition + GraphNodeDefinition

### Faza 2: Execution BC – GraphNodeLinkExecution

1. VO: `GraphNodeLinkExecutionId` w `shell/domain/execution/aggregates/graph_node_link_execution/value_objects/`
2. Agregat: `GraphNodeLinkExecution` w `shell/domain/execution/aggregates/graph_node_link_execution/`
3. Event: `GraphNodeLinkExecutionCreatedEvent`
4. Port repozytorium: `GraphNodeLinkExecutionRepository`
5. Model SQL: `GraphNodeLinkExecutionModel`
6. Repozytorium SQL: `SqlGraphNodeLinkExecutionRepository`
7. Repozytorium InMemory: `InMemoryGraphNodeLinkExecutionRepository`
8. Mapper w mappers execution
9. Migracja: tworzy tabelę `graph_node_link_execution`

### Faza 3: Zmiany w istniejących agregatach

#### GraphNodeDefinition (Definition BC)
- Usunąć `_graph_definition_id` z `__slots__`, `__init__`, `restore()`, `create()`
- Usunąć property `graph_definition_id`
- Usunąć `graph_definition_id` z `GraphNodeDefinitionCreatedEvent`

#### GraphDefinition (Definition BC)
- Usunąć `_graph_node_definition_ids` z `__slots__`, `__init__`, `restore()`, `create()`
- Usunąć property `graph_node_definition_ids`
- Usunąć z mappera model→entity (linie 53, 64)

#### GraphNodeDefinitionModel
- Usunąć kolumnę `graph_definition_id` i FK

#### GraphDefinitionModel
- Usunąć relationship `graph_node_execution_models`

#### GraphExecution (Execution BC)
- Usunąć `_graph_node_definition_execution_slots`
- Usunąć `initialize()` (lub uprościć)
- Usunąć `prepare_node_definitions()`
- Usunąć `attach_node_execution()`
- Usunąć property `graph_node_definition_execution_slots`, `graph_node_definition_executions`
- Uprościć `GraphExecutionInitializedEvent` (bez `graph_node_definition_ids`)

#### GraphNodeExecution (Execution BC)
- Usunąć `_graph_execution_id`
- Usunąć z `__init__`, `restore()`, `new()`
- Usunąć property `graph_execution_id`

#### GraphExecutionModel
- Usunąć kolumnę `graph_node_definition_executions` (JSONB)
- Usunąć relationship `graph_node_execution_models`

#### GraphNodeExecutionModel
- Usunąć kolumnę `graph_execution_id` i FK

### Faza 4: Aktualizacja handlerów

#### BuildGraphExecutionOnTaskExecutionCreatedEventHandler
- Uprościć: nie generować `graph_node_definition_ids`
- Tworzyć GraphExecution przez prostszy konstruktor
- Emitować `GraphExecutionCreatedEvent` zamiast `GraphExecutionInitializedEvent`

#### Saga GraphExecution Saga
- `GraphExecutionInitializedHandler` → zmienić na nasłuchiwanie `GraphExecutionCreatedEvent`
- W handlerze sagi: przez `GraphNodeLinkDefinitionRepository` pobrać node_def_ids
- Dla każdego node_def → emitować `CreateGraphNodeExecutionCommand`
- `GraphNodeExecutionInitializedHandler` → zmienić na tworzenie `GraphNodeLinkExecution`
- Gdy wszystkie linki utworzone → saga COMPLETED

#### SubGraphSpawnRequestedHandler
- Nie używać `prepare_node_definitions()` i `attach_node_execution()`
- Zamiast tego tworzyć GraphExecution, GraphNodeExecution, GraphNodeLinkExecution

#### GraphNodeExecutionCreateHandler
- Uprościć: GraphNodeExecution już nie potrzebuje `graph_execution_id`
- Emitować nowy event `GraphNodeExecutionCreatedEvent` (lub zmienić istniejący)

#### Attach → usunąć
- `AttachGraphNodeExecutionsCommand` → do usunięcia
- `GraphNodeExecutionAttachHandler` → do usunięcia

### Faza 5: Testy

Aktualizacja wszystkich testów:

1. `tests/execution/e2e/cli/test_saga_flow_build_to_ready.py` – gruntowna zmiana
2. `tests/process/unit/graph_execution_saga/test_graph_execution_initialized_handler.py`
3. `tests/process/unit/graph_execution_saga/test_graph_node_execution_initialized_handler.py`
4. Wszystkie testy jednostkowe domeny (GraphDefinition, GraphNodeDefinition, GraphExecution, GraphNodeExecution)
5. Testy integracyjne SQL
6. Testy e2e

## Uwagi

- `GraphNodeTransitionDefinition` nadal reference `graph_node_definition.id` bezpośrednio – to poprawne, bo to reguła biznesowa, nie relacja parent-child
- `GraphNodeTransitionExecution` nadal reference `graph_node_execution.id` bezpośrednio – j.w.
- `GraphExecution.graph_definition_id` pozostaje jako ref do definicji
