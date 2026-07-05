# Ruff Lint Fix Plan — 314 remaining errors (244 already auto-fixed)

## Status

- **Phase B** ✅ Auto-fix completed: `ruff check --fix` fixed 244 errors (I001 import sorting, F541 f-strings, SIM108/110/102 simplifications, B905 zip strict).
- **Remaining**: 314 errors across TC002/TC003, TC004, F841, F401, E402, F821, F403, F811, B017.

---

## C — Manual Structural Fixes

### C1. `in_memory_unit_of_work.py` — Fix E402 (25 errors)

**Problem**: `TRepository = TypeVar("TRepository")` on line 7 splits the import block. All 25 subsequent imports trigger E402.

**Fix**: Move line 7 (`TRepository = TypeVar("TRepository")`) to just before the class definition (after line 107, before line 110).

```python
# Before (lines 3-7):
from typing import TypeVar
from shell.application.platform.ports.unit_of_work import UnitOfWork

TRepository = TypeVar("TRepository")    # <-- wrong place
from shell.domain.definition... import ...

# After:
from typing import TypeVar
from shell.application.platform.ports.unit_of_work import UnitOfWork

from shell.domain.definition... import ...
# ... all other imports ...

TRepository = TypeVar("TRepository")    # <-- moved here, before class

class InMemoryUnitOfWork(UnitOfWork):
```

---

### C2. `node_execution_run_handler.py` — Fix F841 (6 unused vars)

**Problem**: Lines 54-78 assign variables that are never read.

**Fix**: Remove these unused assignments:

```python
# Before (lines 53-55):
workflow_id = WorkflowId(run_node_execution_command.workflow_id)
node_execution_id = NodeExecutionId(run_node_execution_command.node_execution_id)  # UNUSED
now = self._clock.now()  # UNUSED

# After:
workflow_id = WorkflowId(run_node_execution_command.workflow_id)
```

Also remove unused variables in try/except (lines 70-78). The entire `try` block can be simplified since `stdout`, `stderr`, `node_status`, `failure_reason` are all assigned but never used:

```python
# Replace lines 64-78 with:
try:
    await self._strategy.execute(
        node_execution_id=run_node_execution_command.node_execution_id,
        workspace_path=run_node_execution_command.workspace_path,
        runner=self._runner,
    )
except Exception:
    pass
```

---

### C3. `infrastructure_container.py:122` — Fix F821

**Problem**: `session_factory` is a `dependency-injector` provider attribute (class-level), not a regular Python variable. Ruff's static analysis can't resolve it.

**Fix**: Add `# noqa: F821`:

```python
session=providers.Factory(lambda: session_factory()()),  # type: ignore[name-defined]  # noqa: F821
```

---

### C4. `sql_alchemy_uow.py:195` — Fix F841

**Problem**: `message_outbox = OutboxMessageModel(...)` assigned but never read.

**Fix**: Remove the assignment, keep just the constructor call (it may have side effects via the session):

```python
# Before:
message_outbox = OutboxMessageModel(...)
self._active_session.add(message_outbox)

# After:
self._active_session.add(OutboxMessageModel(...))
```

---

### C5. `planner_result_handler.py:92` — Fix F841

**Problem**: `expected_count = len(definition.node_execution_definitions)` assigned but never used.

**Fix**: Remove the assignment:

```python
# Before:
expected_count = len(definition.node_execution_definitions)

# After:
# (remove the line entirely)
```

---

### C6. `node_execution_worker.py:230` — Fix F841

**Problem**: `current_graph_execution = graph_executions[0] if graph_executions else None` assigned but never used.

**Fix**: Remove the assignment.

---

### C7. `propagate_subgraph_results_to_parent.py:44` — Fix F841

**Problem**: `now = self._clock.now()` assigned but never used.

**Fix**: Remove the assignment.

---

### C8. `test_pg_node_result_repository.py:54` — Fix F841

**Problem**: `handler = NodeExecutionSaveResultHandler(...)` assigned but never used.

**Fix**: Remove the assignment.

---

### C9. `test_manager.py:50` — Fix F841

**Problem**: `saga = await manager.create_saga(...)` assigned but never used.

**Fix**: Remove the assignment (use `_` or remove line).

---

### C10. Other unused variables

| File | Line | Variable | Action |
|------|------|----------|--------|
| `test_mappers_round_trip.py` | 37 | `TaskExecutionName` (import) | Remove import |
| `test_mappers_round_trip.py` | 44 | `CreatedAt` (duplicate import) | Remove duplicate |
| `test_mappers_round_trip.py` | 48 | `ProjectId` (import) | Remove import |
| `test_mappers_round_trip.py` | 50 | `UserId` (import) | Remove import |
| `_arch_helpers.py` | 54 | `body` (variable) | Remove assignment |
| `test_mapper_structure.py` | 83 | `func_lines` (variable) | Remove assignment |
| `test_enterprise_patterns.py` | 51 | `test_id` (variable) | Remove assignment |
| `test_message.py` | 134 | `later` (variable) | Remove assignment |

---

### C11. Event files — remove unused `datetime` in TYPE_CHECKING (F401)

Files where `from datetime import datetime` is imported under `TYPE_CHECKING` but never used:

| File |
|------|
| `domain/execution/aggregates/graph_execution/events/graph_execution_completed_event.py` |
| `domain/execution/aggregates/graph_execution/events/graph_execution_planned_event.py` |
| `domain/execution/aggregates/graph_execution/events/graph_execution_sub_graph_settled_event.py` |
| `domain/execution/aggregates/graph_execution/events/graph_execution_sub_graph_spawn_requested_event.py` |
| `domain/execution/aggregates/node_execution/events/node_execution_completed_event.py` |
| `domain/execution/aggregates/task_execution/events/task_execution_created_event.py` |

**Fix**: Remove the `from datetime import datetime` line from each `TYPE_CHECKING` block.

Also remove `httpx` from TYPE_CHECKING in:
- `tests/execution/unit/infrastructure/test_graph_execution_definition_provider_http_adapter.py`
- `tests/execution/unit/infrastructure/test_session_query_service_http_adapter.py`
- `tests/project/unit/infrastructure/test_project_acl_http_adapter.py`
- `tests/user/unit/infrastructure/test_user_acl_http_adapter.py`

Also remove unused `has_method` from:
- `tests/platform/architecture/test_domain_structure.py`
- `tests/platform/architecture/test_regressions.py`

Also remove unused `Generic` from:
- `domain/platform/ports/repository_port.py`

Also remove unused `MaxIterations`, `TaskExecutionName` from:
- `infrastructure/execution/persistence/sql/mappers/__init__.py`

Also remove unused `SqlGraphExecutionStateOutputRepository` from:
- `infrastructure/platform/persistence/sql_alchemy_uow.py`

Also remove unused `datetime.UTC`, `datetime.datetime` from:
- `infrastructure/definition/persistence/sql/mappers/__init__.py`

---

### C12. `conftest.py` — Fix F403 + E402

**Problem**: `from shell.tests.conftest_helpers import *` (F403) + imports after the star import line (E402).

**Fix**: Replace `import *` with explicit imports. Move the SQL-related imports above the star import.

```python
# Current structure (simplified):
from shell.tests.conftest_helpers import *          # line 25 — F403

# ... blank lines ...
import os                                           # line 41 — E402

# ... later ...
from typing import TYPE_CHECKING                   # line 130 — E402
from shell.infrastructure... import ...

# Fixed structure:
from shell.tests.conftest_helpers import (
    _NOW, _build_graph_execution, _make_result_handler,
    _make_task_with_graph_execution, _make_worker,
    _persist_running_workflow, _run_tasker_full,
)                                                   # explicit imports only
```

---

### C13. `test_saga_flow_build_to_ready.py:289` — Fix B007

**Problem**: `cmd_type` in `for cmd_type, payload in created_cmds:` is unused.

**Fix**: Rename to `_cmd_type`:
```python
for _cmd_type, payload in created_cmds:
```

---

### C14. `test_graph_execution_saga_repository.py:102` — Fix B017

**Problem**: `pytest.raises(Exception)` — blind exception assertion.

**Fix**: Replace with a specific exception type (e.g., the actual exception raised by the repo on duplicate save).

---

## D — TC Violations (bulk)

### D1. TC002 — Move imports into TYPE_CHECKING

**Pattern**: Any file with `from __future__ import annotations` where an import is only used in type annotations should have that import under `if TYPE_CHECKING:`.

**Handlers** (command, event, query):
Files in `shell/application/*/command_handlers/`, `event_handlers/`, `query_handlers/`:
- Move `Command` imports into TYPE_CHECKING
- Move `Dto` imports into TYPE_CHECKING
- Move domain `Event` imports into TYPE_CHECKING
- Keep `Repository` port imports at top level (used in `unit_of_work.repository(RepoType)`)

Example — `create_graph_definition_handler.py`:
```python
# Before:
from shell.application.definition.commands.create_graph_definition_command import (
    CreateGraphDefinitionCommand,
)
from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
# ...

# After:
if TYPE_CHECKING:
    from shell.application.definition.commands.create_graph_definition_command import (
        CreateGraphDefinitionCommand,
    )
    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    # ...
```

**Port query services** — files in `shell/application/*/ports/queries/*.py`:
- Move DTO imports into TYPE_CHECKING

**Domain entities/aggregates** — some domain imports used only in type hints:
- `node_definition.py`: many VO imports only used in type hints → move to TYPE_CHECKING
- `graph_definition_embedding.py`: `CreatedAt` → move to TYPE_CHECKING
- Various event files: event-specific imports → move to TYPE_CHECKING
- `rag_document.py`: `ChunkText`, `Embedding`, `EmbeddingModel` → TYPE_CHECKING
- `graph_execution.py`: `NodeExecutionId`, `TaskExecutionId`, `NodeDefinitionId`, `Reason` → TYPE_CHECKING
- `node_execution.py`: `NodeRole`, `NodeType`, `RetryDelaySeconds`, `TimeoutSeconds`, `Mode` → TYPE_CHECKING
- `machine_state.py` aggregates: `WorkflowId`, `SessionId`, `GraphExecutionId`, etc. → TYPE_CHECKING
- `task_execution.py`: `Reason` → TYPE_CHECKING
- `agent_config_execution.py`: `Config`, `CreatedAt` → TYPE_CHECKING
- `agent_skill_execution.py`: `AgentExecutionId`, `SkillPayload`, `CreatedAt` → TYPE_CHECKING
- `session_execution.py`: `UserExecutionId` → TYPE_CHECKING
- `scheduler_execution.py`: `Timestamp` → TYPE_CHECKING
- `domain_event.py`: `CreatedAt` → TYPE_CHECKING

**Repositories** — protocol files:
- `rag_repository.py`: `ChunkIndex` → TYPE_CHECKING
- `agent_execution_repository.py`: `AgentExecution`, `AgentExecutionId`, `NodeExecutionId`, `ExistsResult` → TYPE_CHECKING
- `agent_skill_execution_repository.py`: `AgentExecutionId`, `AgentSkillExecution`, `AgentSkillExecutionId`, `ExistsResult` → TYPE_CHECKING
- `node_execution_state_repository.py`: `NodeExecutionId`, `NodeExecutionState`, etc. → TYPE_CHECKING
- `node_transition_execution_repository.py`: `GraphExecutionId`, `NodeExecutionId`, etc. → TYPE_CHECKING
- `scheduler_definition_repository.py`: `ExistsResult`, `SourceContext`, `TriggerEventType` → TYPE_CHECKING
- `scheduler_execution_repository.py`: `ExistsResult`, `ExecutionStatus`, `ActionRef`, `CountResult`, `SchedulerDefinitionId` → TYPE_CHECKING
- `session_state_repository.py`: `ExistsResult`, `StateDirection`, `SessionId`, `SessionState`, `SessionStateId` → TYPE_CHECKING
- `task_execution_state_repository.py`: `TaskExecutionId`, etc. → TYPE_CHECKING

**Infrastructure** — in-memory repos:
- Most in-memory repositories import domain types used only in type hints → move to TYPE_CHECKING
- `in_memory_graph_definition_repository.py`: `GraphName` → TYPE_CHECKING
- `in_memory_node_definition_repository.py`: `GraphDefinitionId` → TYPE_CHECKING
- `in_memory_rag_document_repository.py`: `ChunkIndex`, `RagChunk`, `RagDocument`, etc. → TYPE_CHECKING
- `in_memory_runner_config_repository.py`: `PackageName` → TYPE_CHECKING
- `in_memory_message_repository.py`: `Destination`, `Source` → TYPE_CHECKING
- Various state in-memory repos: `GraphExecutionId`, `StateDirection`, `GraphExecutionState`, etc. → TYPE_CHECKING
- `in_memory_workflow_repository.py`: `SessionExecutionId`, `SessionIdRef` → TYPE_CHECKING
- `in_memory_agent_execution_repository.py`: `NodeExecutionId` → TYPE_CHECKING
- `in_memory_agent_skill_execution_repository.py`: `AgentExecutionId` → TYPE_CHECKING
- `in_memory_workflow_state_repository.py`: `WorkflowId`, `StateDirection` → TYPE_CHECKING

**Infrastructure** — SQL repos:
- `sql_graph_definition_repository.py`: `GraphName` → TYPE_CHECKING
- `sql_rag_document_repository.py`: `RagChunk`, `RagDocument`, `ChunkIndex`, `DomainTag`, `Embedding` → TYPE_CHECKING
- `sql_message_repository.py`: `WorkflowReference` → TYPE_CHECKING
- `sql_graph_execution_state_input_repository.py`: `GraphExecutionId`, `StateDirection` → TYPE_CHECKING
- `sql_graph_execution_state_output_repository.py`: `GraphExecutionId`, `StateDirection` → TYPE_CHECKING
- `sql_session_execution_repository.py`: `SessionExecutionId`, `UserExecutionId` → TYPE_CHECKING
- `sql_session_execution_state_repository.py`: `SessionExecutionId`, `StateDirection` → TYPE_CHECKING
- `sql_task_execution_state_repository.py`: `TaskExecutionId`, `StateDirection` → TYPE_CHECKING
- `sql_user_execution_repository.py`: `UserExecutionId` → TYPE_CHECKING
- `sql_user_execution_state_repository.py`: `UserExecutionId`, `StateDirection` → TYPE_CHECKING
- `sql_workflow_repository.py`: `SessionExecutionId`, `SessionIdRef` → TYPE_CHECKING
- `sql_workflow_state_repository.py`: `WorkflowId`, `StateDirection` → TYPE_CHECKING
- `sql_scheduler_definition_repository.py`: `SourceContext`, `TriggerEventType` → TYPE_CHECKING

**Infrastructure** — other:
- `graph_execution_definition_provider_http_adapter.py`: `GraphDefinitionSemanticQuery` → TYPE_CHECKING
- `sql_alchemy_uow.py`: `Message`, `DomainEvent`, `AsyncSession`, `async_sessionmaker` → TYPE_CHECKING
- `in_memory_scheduler_definition_repository.py`: `SourceContext`, `TriggerEventType` → TYPE_CHECKING
- `in_memory_scheduler_execution_repository.py`: `ExecutionStatus`, `ActionRef` → TYPE_CHECKING
- `in_memory_session_state_repository.py`: `StateDirection`, `SessionId` → TYPE_CHECKING
- `in_memory_graph_execution_state_input_repository.py`: `GraphExecutionId`, `StateDirection`, `GraphExecutionState` → TYPE_CHECKING
- `in_memory_graph_execution_state_output_repository.py`: `GraphExecutionId`, `StateDirection`, `GraphExecutionState` → TYPE_CHECKING
- `sql_session_repository.py`: `SessionId` → TYPE_CHECKING

**Tests**:
- `test_sql_task_execution_repository.py`: `SqlAlchemyUnitOfWork` → TYPE_CHECKING
- `test_graph_execution_initialized_handler.py`: `FakeCommandOutboxPublisher`, `FakeLogger`, `InMemoryGraphExecutionSagaRepository` → TYPE_CHECKING
- `test_node_execution_initialized_handler.py`: same → TYPE_CHECKING
- `test_manager.py`: `InMemoryGraphExecutionSagaRepository` → TYPE_CHECKING
- `test_build_graph_execution_on_task_execution_created_event_handler.py`: `GraphDefinitionSemanticQuery` → TYPE_CHECKING
- `conftest.py` (process): `GraphExecutionSagaState` → TYPE_CHECKING

**Saga process**:
- `graph_execution_saga.py`: `GraphExecutionSagaRepository` → TYPE_CHECKING
- `graph_execution_saga_repository.py`: `GraphExecutionSagaState` → TYPE_CHECKING

### D2. TC003 — Move stdlib into TYPE_CHECKING

| File | Import | Fix |
|------|--------|-----|
| `infrastructure/platform/persistence/sql/models/command/inbox_command.py` | `datetime` | Move to TYPE_CHECKING (unless used in Mapped[...] at runtime) |
| `infrastructure/platform/persistence/sql/models/command/outbox_command.py` | `datetime` | Same — check if model uses Mapped[datetime] |
| `infrastructure/scheduling/services/scheduler_service.py` | `Callable`, `Coroutine` | Move to TYPE_CHECKING |
| `process/execution/graph_execution_saga/ports/command_publisher.py` | `datetime` | Move to TYPE_CHECKING |
| `tests/platform/architecture/_arch_helpers.py` | `Iterator` | Move to TYPE_CHECKING |
| `tests/platform/architecture/test_process_structure.py` | `Path` | Move to TYPE_CHECKING |
| `tests/process/conftest.py` | `datetime` | Move to TYPE_CHECKING |
| `application/platform/dto/message.py` | `datetime` | Move to TYPE_CHECKING |

**IMPORTANT**: For SQLAlchemy model files (`inbox_command.py`, `outbox_command.py`), check if `datetime` is used in `Mapped[datetime]` column definitions. If so, add `# noqa: TC003` instead of moving — SQLAlchemy 2.x needs runtime types in model subclasses.

### D3. TC004 — Move imports OUT of TYPE_CHECKING

These imports are hidden in `if TYPE_CHECKING:` blocks but ARE used at runtime (in function bodies, not just type hints):

| File | Imports | Reason |
|------|---------|--------|
| `infrastructure/definition/persistence/sql/mappers/graph_definition_mapper.py` | `NodeDefinitionId`, `NodeTransitionDefinitionId`, `GraphDefinitionModel` | Used in function bodies (constructors, model instantiation) |
| `infrastructure/execution/persistence/sql/mappers/__init__.py` | `GraphExecutionStateInputModel`, `GraphExecutionStateOutputModel` | Used in function bodies |
| `infrastructure/platform/persistence/sql/mappers/message_mappers.py` | `MessageModel` | Used in function body |

**Fix**: Move these imports to top-level (above `if TYPE_CHECKING:`), grouped with the `from __future__ import annotations` block.

---

## E — Cleanup Pass

After applying C and D:

```bash
ruff check --fix --unsafe-fixes shell/
```

The `--unsafe-fixes` removes truly unused imports (F401) that were left behind after TC restructuring.

---

## F — Verification

```bash
cd C:\Users\palysiewicz\IdeaProjects\SHELL
python -m ruff check shell/
# Expected: 0 errors

python -m pytest shell/tests/ -x -q
# Expected: all tests pass
```

---

## A — Prevention (add after cleanup)

### A1. `.pre-commit-config.yaml`

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.11.0
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
```

### A2. `.github/workflows/lint.yml`

```yaml
name: Lint
on: [push, pull_request]
jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff
      - run: ruff check shell/
```

### A3. `shell/pyproject.toml` — add per-file-ignores

```toml
[tool.ruff.lint.per-file-ignores]
# dependency-injector provider attributes look like undefined names
"shell/bootstrap/platform/container/infrastructure_container.py" = ["F821"]
```

---

## Summary of remaining work

| Phase | Type | Files affected | Est. effort |
|-------|------|---------------|-------------|
| C1 | Move TypeVar | 1 | 1 edit |
| C2-C10 | Remove unused | ~15 | ~30 edits |
| C11 | Remove unused imports | ~15 | ~15 edits |
| C12 | Fix star import | 1 | ~10 edits |
| C13-C14 | Minor | 2 | 2 edits |
| D1 | TC002 — move to TYPE_CHECKING | ~80 | ~80 files × 1-5 edits |
| D2 | TC003 — stdlib | ~8 | ~8 edits |
| D3 | TC004 — move out of TYPE_CHECKING | 3 | 3 edits |
| E | `--unsafe-fixes` pass | auto | 1 command |
| A | Pre-commit + CI | 2 files | 2 new files |
