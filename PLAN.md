# Plan: NodeLinkDefinition + NodeLinkExecution

## Cel

Zastąpienie bezpośrednich relacji FK między agregatami parami link-table (wzorzec wielu-do-wielu przez osobny agregat):

| Obecnie (do usunięcia) | Nowy agregat |
|---|---|
| `NodeDefinition.graph_definition_id` FK | `NodeLinkDefinition` |
| `GraphDefinition._node_definition_ids` lista ID | `NodeLinkDefinition` |
| `NodeExecution.graph_execution_id` FK | `NodeLinkExecution` |
| `GraphExecution._node_definition_execution_slots` JSONB | `NodeLinkExecution` |

## Przepływ danych (Execution)

```
1. Event/komenda → tworzy GraphExecution (bez slotów, bez node_executions)
   → emituje GraphExecutionCreatedEvent (tylko graph_execution_id + graph_definition_id)

2. Saga odbiera event → przez provider wyszukuje NodeDefinitionIds
   powiązane z GraphDefinition (przez NodeLinkDefinition)
   → dla każdego emituje CreateNodeExecutionCommand

3. CreateNodeExecutionCommand → tworzy NodeExecution (bez FK do execution)
   → emituje NodeExecutionCreatedEvent (graph_execution_id, node_execution_id)

4. NodeLinkExecutionHandler odbiera event → tworzy NodeLinkExecution
   (łączy GraphExecution + NodeExecution)
   → emituje NodeLinkExecutionCreatedEvent

5. Saga odbiera NodeLinkExecutionCreatedEvent → wie że node jest gotowy
   → gdy wszystkie linki utworzone → kończy sagę, emituje GraphExecutionReadyEvent
```

## Kolejność implementacji

### Faza 1: Definition BC – NodeLinkDefinition

1. VO: `NodeLinkDefinitionId` w `shell/domain/definition/aggregates/node_link_definition/value_objects/`
2. Agregat: `NodeLinkDefinition` w `shell/domain/definition/aggregates/node_link_definition/`
3. Event: `NodeLinkDefinitionCreatedEvent`
4. Port repozytorium: `NodeLinkDefinitionRepository`
5. Model SQL: `NodeLinkDefinitionModel`
6. Repozytorium SQL: `SqlNodeLinkDefinitionRepository`
7. Repozytorium InMemory: `InMemoryNodeLinkDefinitionRepository`
8. Mapper: w `shell/infrastructure/definition/persistence/sql/mappers/`
9. Migracja: tworzy tabelę `node_link_definition`
10. Seed data: migracja dodająca linki dla istniejących GraphDefinition + NodeDefinition

### Faza 2: Execution BC – NodeLinkExecution

1. VO: `NodeLinkExecutionId` w `shell/domain/execution/aggregates/node_link_execution/value_objects/`
2. Agregat: `NodeLinkExecution` w `shell/domain/execution/aggregates/node_link_execution/`
3. Event: `NodeLinkExecutionCreatedEvent`
4. Port repozytorium: `NodeLinkExecutionRepository`
5. Model SQL: `NodeLinkExecutionModel`
6. Repozytorium SQL: `SqlNodeLinkExecutionRepository`
7. Repozytorium InMemory: `InMemoryNodeLinkExecutionRepository`
8. Mapper w mappers execution
9. Migracja: tworzy tabelę `node_link_execution`

### Faza 3: Zmiany w istniejących agregatach

#### NodeDefinition (Definition BC)
- Usunąć `_graph_definition_id` z `__slots__`, `__init__`, `restore()`, `create()`
- Usunąć property `graph_definition_id`
- Usunąć `graph_definition_id` z `NodeDefinitionCreatedEvent`

#### GraphDefinition (Definition BC)
- Usunąć `_node_definition_ids` z `__slots__`, `__init__`, `restore()`, `create()`
- Usunąć property `node_definition_ids`
- Usunąć z mappera model→entity (linie 53, 64)

#### NodeDefinitionModel
- Usunąć kolumnę `graph_definition_id` i FK

#### GraphDefinitionModel
- Usunąć relationship `node_execution_models`

#### GraphExecution (Execution BC)
- Usunąć `_node_definition_execution_slots`
- Usunąć `initialize()` (lub uprościć)
- Usunąć `prepare_node_definitions()`
- Usunąć `attach_node_execution()`
- Usunąć property `node_definition_execution_slots`, `node_definition_executions`
- Uprościć `GraphExecutionInitializedEvent` (bez `node_definition_ids`)

#### NodeExecution (Execution BC)
- Usunąć `_graph_execution_id`
- Usunąć z `__init__`, `restore()`, `new()`
- Usunąć property `graph_execution_id`

#### GraphExecutionModel
- Usunąć kolumnę `node_definition_executions` (JSONB)
- Usunąć relationship `node_execution_models`

#### NodeExecutionModel
- Usunąć kolumnę `graph_execution_id` i FK

### Faza 4: Aktualizacja handlerów

#### BuildGraphExecutionOnTaskExecutionCreatedEventHandler
- Uprościć: nie generować `node_definition_ids`
- Tworzyć GraphExecution przez prostszy konstruktor
- Emitować `GraphExecutionCreatedEvent` zamiast `GraphExecutionInitializedEvent`

#### Saga GraphExecution Saga
- `GraphExecutionInitializedHandler` → zmienić na nasłuchiwanie `GraphExecutionCreatedEvent`
- W handlerze sagi: przez `NodeLinkDefinitionRepository` pobrać node_def_ids
- Dla każdego node_def → emitować `CreateNodeExecutionCommand`
- `NodeExecutionInitializedHandler` → zmienić na tworzenie `NodeLinkExecution`
- Gdy wszystkie linki utworzone → saga COMPLETED

#### SubGraphSpawnRequestedHandler
- Nie używać `prepare_node_definitions()` i `attach_node_execution()`
- Zamiast tego tworzyć GraphExecution, NodeExecution, NodeLinkExecution

#### NodeExecutionCreateHandler
- Uprościć: NodeExecution już nie potrzebuje `graph_execution_id`
- Emitować nowy event `NodeExecutionCreatedEvent` (lub zmienić istniejący)

#### Attach → usunąć
- `AttachNodeExecutionsCommand` → do usunięcia
- `NodeExecutionAttachHandler` → do usunięcia

### Faza 5: Testy

Aktualizacja wszystkich testów:

1. `tests/execution/e2e/cli/test_saga_flow_build_to_ready.py` – gruntowna zmiana
2. `tests/process/unit/graph_execution_saga/test_graph_execution_initialized_handler.py`
3. `tests/process/unit/graph_execution_saga/test_node_execution_initialized_handler.py`
4. Wszystkie testy jednostkowe domeny (GraphDefinition, NodeDefinition, GraphExecution, NodeExecution)
5. Testy integracyjne SQL
6. Testy e2e

## Uwagi

- `NodeTransitionDefinition` nadal reference `node_definition.id` bezpośrednio – to poprawne, bo to reguła biznesowa, nie relacja parent-child
- `NodeTransitionExecution` nadal reference `node_execution.id` bezpośrednio – j.w.
- `GraphExecution.graph_definition_id` pozostaje jako ref do definicji
