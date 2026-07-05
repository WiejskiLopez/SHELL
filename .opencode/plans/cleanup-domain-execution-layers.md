# Cleanup: domain/execution layers

Usunięcie re-export warstw, przeniesienie portów i wyjątków do agregatów.

## Konwencja nazewnicza dla wyjątków (do skilla)

W `class-and-type-naming-standards/SKILL.md`:

**Linia 42 — zmiana:**
```
| Domain Exception | `PascalCase + Error` | `GraphExecutionNotFoundError`, `InvalidNodeStateError`, `MaxStepExceeded` |
```

**Nowa sekcja po tabeli klas domenowych (za linią 42):**

```markdown
### Domain Exception — szczególne zasady

```
<AggregateName><CoZaBlad>Error
```

- `AggregateName` — nazwa agregatu (np. `GraphExecution`, `NodeExecution`, `Workflow`)
- `CoZaBlad` — opis błędu w PascalCase (np. `NotFound`, `InvalidState`, `MaxStepExceeded`, `RoleNotResolvable`)
- Sufiks `Error` — obowiązkowy

Przykłady:
| Klasa | Opis |
|-------|------|
| `GraphExecutionNotFoundError` | GraphExecution nie znaleziony |
| `GraphExecutionGraphDefinitionNotFoundError` | GraphDefinition nie znaleziony przez graph_execution |
| `NodeExecutionNotFoundError` | NodeExecution nie znaleziony |
| `NodeExecutionInvalidStateError` | Nieprawidłowy stan NodeExecution |
| `WorkflowInvalidTransitionError` | Nieprawidłowa tranzycja Workflow |
| `NodeExecutionMaxStepExceededError` | Przekroczony max step w NodeExecution |
| `NodeExecutionRoleNotResolvableError` | Rola nierozwiązywalna w NodeExecution |

- NotFound zawsze z sufiksem `Error`
- Invalid state/transition zawsze z sufiksem `Error`
- Wyjątki definiuje się w agregacie którego dotyczą, w katalogu `aggregates/{agregat}/exceptions/`
```

---

## Krok 1: DELETE `domain/execution/repositories/`

Usunąć `shell/domain/execution/repositories/__init__.py` — 10 re-exportów, 0 importerów.
Usunąć katalog `repositories/`.

---

## Krok 2: DELETE `domain/execution/events/`

Usunąć `shell/domain/execution/events/__init__.py` — 17 re-exportów.
Usunąć katalog `events/`.

Każdy z 33 importerów przechodzi na import z `aggregates.{aggregate}.events.{nazwa_pliku}`.

Mapowanie event → aggregate:
| Event | Import docelowy |
|---|---|
| `GraphExecutionConstructedEvent` | `aggregates.graph_execution.events.graph_execution_constructed_event` |
| `GraphExecutionInitializedEvent` | `aggregates.graph_execution.events.graph_execution_initialized_event` |
| `GraphExecutionStateChangedEvent` | `aggregates.graph_execution_state.events.graph_execution_state_changed_event` |
| `NodeExecutionAdvancedEvent` | `aggregates.workflow.events.node_execution_advanced_event` |
| `NodeExecutionCompletedEvent` | `aggregates.node_execution.events.node_execution_completed_event` |
| `NodeExecutionFailedEvent` | `aggregates.node_execution.events.node_execution_failed_event` |
| `NodeExecutionInitializedEvent` | `aggregates.node_execution.events.node_execution_initialized_event` |
| `NodeExecutionRequestedEvent` | `aggregates.workflow.events.node_execution_requested_event` |
| `NodeExecutionTimeoutExpiredEvent` | `aggregates.node_execution.events.node_execution_timeout_expired_event` |
| `SessionExecutionCreatedEvent` | `aggregates.session_execution.events.session_execution_created_event` |
| `TaskExecutionCompletedEvent` | `aggregates.task_execution.events.task_execution_completed_event` |
| `TaskExecutionCreatedEvent` | `aggregates.task_execution.events.task_execution_created_event` |
| `UserExecutionCreatedEvent` | `aggregates.user_execution.events.user_execution_created_event` |
| `WorkflowAbortedEvent` | `aggregates.workflow.events.workflow_aborted_event` |
| `WorkflowCompletedEvent` | `aggregates.workflow.events.workflow_completed_event` |
| `WorkflowFailedEvent` | `aggregates.workflow.events.workflow_failed_event` |
| `WorkflowStartedEvent` | `aggregates.workflow.events.workflow_started_event` |
| `DomainEvent` | `shell.domain.platform.events` (już stamtąd) |

### Konsumenci do aktualizacji (33):

**Aplikacja (4):**
1. `application/execution/event_handlers/node_execution_completed_handler.py`
2. `application/execution/event_handlers/node_execution_worker.py`
3. `application/execution/event_handlers/notify_parent_on_child_completion_handler.py`
4. `application/execution/event_handlers/build_graph_execution_on_task_execution_created_event_handler.py`

**Infra/Bootstrap (2):**
5. `bootstrap/platform/factory/event_factory.py`
6. `infrastructure/platform/serialization/event_deserializer.py`

**Testy (27):**
7. `tests/execution/e2e/cli/test_run_tasker_workflow_partial_failure.py`
8. `tests/execution/e2e/cli/test_run_tasker_workflow_happy_path.py`
9. `tests/execution/e2e/cli/test_run_tasker_workflow_edge_cases.py`
10. `tests/execution/e2e/cli/test_saga_flow_build_to_ready.py`
11. `tests/execution/conftest.py`
12. `tests/definition/conftest.py`
13. `tests/platform/conftest.py`
14. `tests/conftest_helpers.py`
15. `tests/execution/unit/application/test_node_execution_worker_idempotency.py`
16. `tests/execution/unit/application/test_node_execution_worker_happy_path.py`
17. `tests/execution/unit/application/test_node_execution_worker_failure.py`
18. `tests/execution/unit/application/test_node_execution_result_handler.py`
19. `tests/execution/unit/application/test_workflow_start_handler.py`
20. `tests/execution/unit/application/test_task_execution_import_handler.py`
21. `tests/execution/unit/application/test_build_graph_execution_on_task_execution_created_event_handler.py`
22. `tests/execution/unit/domain/test_start_at.py`
23. `tests/execution/unit/domain/test_graph_execution_state_output.py`
24. `tests/execution/unit/domain/test_graph_execution_state_input.py`
25. `tests/execution/unit/domain/test_finish.py`
26. `tests/execution/unit/domain/test_abort.py`
27. `tests/platform/unit/application/test_outbox.py`
28. `tests/platform/integration/sql_sqlite/test_transactional_outbox.py`
29. `tests/platform/integration/sql_sqlite/test_sql_outbox_publisher.py`
30. `tests/platform/integration/sql_sqlite/test_sql_audit_publisher.py`
31. `tests/platform/integration/sql_sqlite/test_outbox_to_inbox_relay.py`
32. `tests/process/unit/graph_execution_saga/test_node_execution_initialized_handler.py`
33. `tests/process/unit/graph_execution_saga/test_graph_execution_initialized_handler.py`

---

## Krok 3: DELETE + MOVE `domain/execution/exceptions/`

### 3a. Pliki do usunięcia
- `shell/domain/execution/exceptions/__init__.py`
- `shell/domain/execution/exceptions/graph_definition_not_found.py`
- `shell/domain/execution/exceptions/node_not_found.py`
- Katalog `exceptions/`

### 3b. Nowy plik: `graph_execution/exceptions/graph_definition_not_found_error.py`

```python
from shell.domain.platform.exceptions.domain_error import DomainError


class GraphExecutionGraphDefinitionNotFoundError(DomainError):
    def __init__(self, query: str) -> None:
        self.query = query
        super().__init__(f'Graph definition not found for query: {query}')
```

Dodać export w `graph_execution/exceptions/__init__.py`.

### 3c. Nowy plik: `node_execution/exceptions/node_not_found_error.py`

```python
from shell.domain.platform.exceptions.domain_error import DomainError


class NodeExecutionNotFoundError(DomainError):
    def __init__(self, node_execution_id: str) -> None:
        self.node_execution_id = node_execution_id
        super().__init__(f'Node execution not found: {node_execution_id}')
```

Dodać export w `node_execution/exceptions/__init__.py`.

### 3d. Konsumenci do aktualizacji (13):

| Plik | Stary import | Nowy import |
|---|---|---|
| `strategies/node_execution_strategy/registry.py` | `from ...exceptions import InvalidNodeMode` | `from ...aggregates.node_execution.exceptions.invalid_node_mode import InvalidNodeMode` |
| `command_handlers/node_execution_run_handler.py` | `from ...exceptions import WorkflowNotFound` | `from ...aggregates.workflow.exceptions.workflow_not_found import WorkflowNotFound` |
| `command_handlers/edge_link_execution_update_handler.py` | `from ...exceptions import EdgeLinkExecutionNotFoundError` | `from ...aggregates.edge_link_execution.exceptions.edge_link_execution_not_found_error import EdgeLinkExecutionNotFoundError` |
| `command_handlers/edge_link_execution_delete_handler.py` | jw. | jw. |
| `command_handlers/edge_execution_update_handler.py` | `from ...exceptions import EdgeExecutionNotFoundError` | `from ...aggregates.edge_execution.exceptions.edge_execution_not_found_error import EdgeExecutionNotFoundError` |
| `command_handlers/edge_execution_delete_handler.py` | jw. | jw. |
| `framework/platform/api/middleware/error_handler.py` | `from ...exceptions import NodeNotFound, TaskExecutionNotFound, WorkflowNotFound` | `from ...aggregates.node_execution.exceptions.node_not_found_error import NodeExecutionNotFoundError` + reszta z agregatów |
| `framework/execution/api/routers/edge_link_executions/controller.py` | `from ...exceptions import EdgeLinkExecutionNotFoundError` | `from ...aggregates.edge_link_execution.exceptions...` |
| `framework/execution/api/routers/edge_executions/controller.py` | `from ...exceptions import EdgeExecutionNotFoundError` | `from ...aggregates.edge_execution.exceptions...` |
| `infrastructure/execution/default_implementations/sub_graph_defaults.py` | `from ...exceptions import GraphDefinitionNotFound` | `from ...aggregates.graph_execution.exceptions.graph_definition_not_found_error import GraphExecutionGraphDefinitionNotFoundError` |
| `tests/execution/unit/domain/test_abort.py` | `from ...exceptions import InvalidWorkflowTransition` | `from ...aggregates.workflow.exceptions...` |
| `tests/execution/unit/domain/test_finish.py` | jw. | jw. |
| `tests/execution/unit/domain/test_graph_execution_routing_service.py` | `from ...exceptions import RoleNotResolvable` | `from ...aggregates.node_execution.exceptions...` |

---

## Krok 4: MOVE `domain/execution/ports/` → `graph_execution/aggregate/ports/`

### 4a. Pliki do przeniesienia (zawartość bez zmian, poza importem DomainError w sub_graph_policy):

1. `ports/sub_graph_discovery.py` → `aggregates/graph_execution/ports/sub_graph_discovery.py`
2. `ports/sub_graph_governance.py` → `aggregates/graph_execution/ports/sub_graph_governance.py`
3. `ports/sub_graph_observer.py` → `aggregates/graph_execution/ports/sub_graph_observer.py`
4. `ports/sub_graph_policy.py` → `aggregates/graph_execution/ports/sub_graph_policy.py` (aktualizacja importu `GraphDefinitionNotFound` → `GraphExecutionGraphDefinitionNotFoundError`)
5. `ports/sub_graph_security.py` → `aggregates/graph_execution/ports/sub_graph_security.py`
6. `ports/sub_graph_versioning.py` → `aggregates/graph_execution/ports/sub_graph_versioning.py`

Usunąć `shell/domain/execution/ports/` katalog.

Aktualizować `aggregates/graph_execution/ports/__init__.py` — dodać exporty dla nowych portów.

### 4b. Konsumenci do aktualizacji (3):

| Plik | Stary import | Nowy import |
|---|---|---|
| `event_handlers/sub_graph_spawn_requested_handler.py` | `from shell.domain.execution.ports.sub_graph_governance` etc. | `from shell.domain.execution.aggregates.graph_execution.ports.sub_graph_governance` etc. |
| `event_handlers/planner_result_handler.py` | `from shell.domain.execution.ports.sub_graph_discovery` | `from shell.domain.execution.aggregates.graph_execution.ports.sub_graph_discovery` |
| `infrastructure/execution/default_implementations/sub_graph_defaults.py` | wszystkie 6 portów | wszystkie z `aggregates.graph_execution.ports` |

### 4c. Update w `sub_graph_policy.py`:

Import `GraphDefinitionNotFound` zmienić na `GraphExecutionGraphDefinitionNotFoundError` z nowej lokalizacji.

---

## Krok 5: Skill update

Edycja `class-and-type-naming-standards/SKILL.md`:
- Linia 42: zmiana wzorca i przykładu
- Nowa sekcja "Domain Exception — szczególne zasady" z tabelą przykładów

---

## Krok 6: Weryfikacja

Po wszystkich zmianach:
1. Uruchomić `mypy shell/` — sprawdzić typy
2. Uruchomić testy `pytest tests/` — sprawdzić czy importy działają
3. `git diff --stat` — podsumowanie zmienionych plików
