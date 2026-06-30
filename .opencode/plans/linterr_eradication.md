# Lint Error Eradication Plan

## Problem

531 ruff errors. `--fix` cleared 244 (I001, F541, SIM). **314 remain.**

---

## Strategy

Three categories, one approach: **fix the code properly, no blinders.**

| # | Category | Count | Approach |
|---|----------|-------|----------|
| 1 | **E402** (import not at top) | 25 | Fix structural issue in 1 file |
| 2 | **F841/F401** (unused vars/imports) | ~50 | Remove dead code. Where missing logic is found → implement it |
| 3 | **TC002/003/004** (type-checking imports) | ~200 | Move imports between TYPE_CHECKING and top-level as appropriate |
| 4 | **Rests** (F821, B007, B017, F403, SIM) | ~15 | Fix each |
| 5 | **Arch test** | 1 new file | Fail CI if lint regresses |

---

## 1. E402 — `in_memory_unit_of_work.py` (25 errors)

**Root cause**: `TRepository = TypeVar("TRepository")` on line 7 breaks the import block. All 25 subsequent imports trigger E402.

**Fix**: Move the TypeVar assignment to line 109 — immediately before the class definition, after all imports.

Current structure:
```python
from __future__ import annotations
from typing import TypeVar
from shell.application... import ...
TRepository = TypeVar("TRepository")        # ← WRONG (line 7)
from shell.domain.definition...import ...   # ← E402
from shell.domain.execution... import ...   # ← E402
# ... 23 more imports ...
```

Fixed structure:
```python
from __future__ import annotations
from typing import TypeVar
from shell.application... import ...
from shell.domain.definition... import ...
from shell.domain.execution... import ...
# ... all 27 imports ...

TRepository = TypeVar("TRepository")        # ← MOVED (line ~109)

class InMemoryUnitOfWork(UnitOfWork):       # line 110
```

**Files touched**: 1

---

## 2. Unused variables/imports (F841/F401)

### 2a. `graph_node_execution_run_handler.py` — 6 F841

**Root cause**: The method documents calling `Workflow.record_graph_node_execution_result` but that method does not exist. The handler is a **stub**: it loads then saves the workflow twice with no mutations, creates IDs it never uses, captures stdout/stderr/status/failure_reason but discards them, and returns `""`.

**Fix**: Implement the correct logic. The handler should:

1. Mark `GraphNodeExecution` as `RUNNING` → `start(now)`
2. Execute the strategy → `ExecutionResult`
3. On success: `node.complete(result, now)`; create `GraphNodeExecutionState` with direction OUT containing stdout/stderr
4. On failure: `node.fail(error, now)`; create state with error info
5. Save both aggregates, stage events from both, return result ID

**Approximate implementation:**

```python
async def handle(self, run_graph_node_execution_command: RunGraphNodeExecutionCommand) -> str:
    workflow_id = WorkflowId(run_graph_node_execution_command.workflow_id)
    graph_node_execution_id = GraphNodeExecutionId(run_graph_node_execution_command.graph_node_execution_id)

    async with self._unit_of_work as unit_of_work:
        workflow = await unit_of_work.repository(WorkflowRepository).get_by_id(workflow_id)
        if workflow is None:
            raise WorkflowNotFound(run_graph_node_execution_command.workflow_id)

        node = await unit_of_work.repository(GraphNodeExecutionRepository).get_by_id(graph_node_execution_id)
        if node is None:
            raise WorkflowNotFound(f"GraphNodeExecution {graph_node_execution_id} not found")

        now = self._clock.now()
        node.start(now)
        await unit_of_work.repository(GraphNodeExecutionRepository).save(node)
        unit_of_work.stage_events(node.pull_events())

    try:
        exec_result = await self._strategy.execute(
            graph_node_execution_id=run_graph_node_execution_command.graph_node_execution_id,
            workspace_path=run_graph_node_execution_command.workspace_path,
            runner=self._runner,
        )
    except Exception as exc:
        result_id = await self._save_failure(
            graph_node_execution_id, workflow_id, ErrorDescription(str(exc))
        )
        return result_id

    result_id = await self._save_success(
        graph_node_execution_id, workflow_id,
        ExecutionStdout(exec_result.stdout) if exec_result.stdout else None,
        ExecutionStderr(exec_result.stderr) if exec_result.stderr else None,
    )
    return result_id
```

(Plus `_save_success` and `_save_failure` helpers following the `GraphNodeExecutionSaveResultHandler` pattern.)

**Files touched**: 1 (with significant logic addition)

### 2b. Other F841 — purely unused variables

| File | Variable | Action |
|------|----------|--------|
| `propagate_subgraph_results_to_parent.py:44` | `now` | Remove assignment |
| `planner_result_handler.py:92` | `expected_count` | Remove assignment |
| `graph_node_execution_worker.py:230` | `current_graph_execution` | Remove assignment |
| `sql_alchemy_uow.py:195` | `message_outbox` | Inline `OutboxMessageModel(...)` into `.add()` |
| `_arch_helpers.py:54` | `body` | Remove assignment (unused in function) |
| `test_mapper_structure.py:83` | `func_lines` | Remove assignment |
| `test_enterprise_patterns.py:51` | `test_id` | Remove assignment |
| `test_message.py:134` | `later` | Remove assignment |
| `test_pg_node_result_repository.py:54` | `handler` | Remove assignment |
| `test_manager.py:50` | `saga` | Remove assignment |

### 2c. F401 — unused imports (easy)

| File | Import | Action |
|------|--------|--------|
| 6 event files under `domain/execution/aggregates/*/events/` | `datetime` under `TYPE_CHECKING` | Remove (import was added but never referenced) |
| 4 test infrastructure files | `httpx` under `TYPE_CHECKING` | Remove |
| `test_*.py` (2 files) | `has_method` | Remove |
| `repository_port.py` | `Generic` | Remove |
| `sql/mappers/__init__.py` (execution) | `MaxIterations`, `TaskExecutionName` | Remove |
| `sql/mappers/__init__.py` (definition) | `UTC`, `datetime` | Remove |
| `sql_alchemy_uow.py` | `SqlGraphExecutionStateOutputRepository` | Remove |
| `test_mappers_round_trip.py` | `TaskExecutionName`, `CreatedAt` (dup), `ProjectId`, `UserId` | Remove duplicate + unused |
| `test_*.py` (4 files) | `GraphExecutionStateOutputModel` | Remove (already imported via different path) |

**Files touched**: ~20

---

## 3. TC violations (~200 errors)

### 3a. TC002 — Move into TYPE_CHECKING (~80 files, ~180 errors)

**Pattern**: Any file with `from __future__ import annotations` where an import is ONLY used in type annotations (class/method signatures, Protocol return types, dataclass fields).

**Safe to move**: Commands, DTOs, Domain Events, Value Objects, Entity classes — when used only in annotations.

**NOT safe to move** (keep at top level):
- Repository ports (used in `unit_of_work.repository(RepoType)` as runtime arg)
- Imports used in function/method **bodies** (constructors, isinstance, type() calls)
- `Protocol` and `ABC` base classes
- `Exception` subclasses (used in `raise` and `except`)
- SQLAlchemy `Mapped`, `mapped_column`, `declared_attr` (needed at runtime by ORM)

**Process for each file**:
1. For each top-level import, check if it's used only in type annotations
2. If yes → move to existing or new `if TYPE_CHECKING:` block
3. If it IS used in function bodies → leave at top level (ruff will stop complaining because the import IS used at runtime beyond annotations)

**Concrete example — handler pattern**:

```python
# BEFORE
from shell.application.XXX.commands.FooCommand import FooCommand        # only in handle() signature
from shell.domain.YYY.aggregates.ZZZ import ZZZ                        # only in handle() signature
from shell.domain.YYY.repositories.ZZZ import ZZZRepository            # used in unit_of_work.repository() — KEEP at top

# AFTER
if TYPE_CHECKING:
    from shell.application.XXX.commands.FooCommand import FooCommand
    from shell.domain.YYY.aggregates.ZZZ import ZZZ
# ZZZRepository stays at top level
```

### 3b. TC003 — Stdlib into TYPE_CHECKING (~8 files, ~8 errors)

| File | Import | Action |
|------|--------|--------|
| `shell/infrastructure/platform/persistence/sql/models/command/inbox_command.py` | `datetime` | Check if used in `Mapped[datetime]` → if yes, `# noqa: TC003` (SQLAlchemy needs runtime type). If no, move to TYPE_CHECKING |
| `shell/infrastructure/platform/persistence/sql/models/command/outbox_command.py` | `datetime` | Same check |
| `shell/infrastructure/scheduling/services/scheduler_service.py` | `Callable`, `Coroutine` | Move to TYPE_CHECKING |
| `shell/process/execution/graph_execution_saga/ports/command_publisher.py` | `datetime` | Move to TYPE_CHECKING |
| `shell/tests/platform/architecture/_arch_helpers.py` | `Iterator` | Move to TYPE_CHECKING |
| `shell/tests/platform/architecture/test_process_structure.py` | `Path` | Move to TYPE_CHECKING |
| `shell/tests/process/conftest.py` | `datetime` | Move to TYPE_CHECKING |
| `shell/application/platform/dto/message.py` | `datetime` | Move to TYPE_CHECKING |

For the SQL model files: `from __future__ import annotations` means ALL annotations are strings, so `Mapped[datetime]` as a type hint does NOT need `datetime` at runtime. HOWEVER, if the file uses `datetime` in default value expressions like `default=datetime.utcnow` in `mapped_column()`, it needs it at runtime. Check each file.

### 3c. TC004 — Move OUT of TYPE_CHECKING (3 files, 3 errors)

These imports are currently (incorrectly) inside `if TYPE_CHECKING:` blocks but ARE used at runtime in function bodies:

| File | Import | Why used at runtime |
|------|--------|-------------------|
| `infrastructure/definition/persistence/sql/mappers/graph_definition_mapper.py` | `GraphNodeDefinitionId`, `GraphNodeTransitionDefinitionId`, `GraphDefinitionModel` | Called in mapper functions: `GraphNodeDefinitionId(nd.id)`, `GraphDefinitionModel(id=...)` |
| `infrastructure/execution/persistence/sql/mappers/__init__.py` | `GraphExecutionStateInputModel`, `GraphExecutionStateOutputModel` | Called in mapper functions: `GraphExecutionStateInputModel(id=...)` |
| `infrastructure/platform/persistence/sql/mappers/message_mappers.py` | `MessageModel` | Called in mapper: `MessageModel(id=...)` |

**Fix**: Move these imports to top level (above `if TYPE_CHECKING:`).

---

## 4. Remaining one-off fixes

| File | Rule | Fix |
|------|------|-----|
| `infrastructure_container.py:122` | F821 | `session_factory` is a `dependency-injector` provider attribute. Change `lambda: session_factory()()` to `lambda: build_session_factory(self.config.db_url)()`. Eliminates the F821 without noqa. |
| `test_saga_flow_build_to_ready.py:289` | B007 | Rename `cmd_type` → `_cmd_type` |
| `test_graph_execution_saga_repository.py:102` | B017 | Replace `pytest.raises(Exception)` with the actual exception class the repo raises (e.g., `UniqueViolation` or `IntegrityError`) |
| `conftest.py:25` | F403 | Replace `from shell.tests.conftest_helpers import *` with explicit named imports |
| `conftest.py:41-135` | E402 | Move SQL-related imports (`os`, `bootstrap_database`, `ShellConfig`, etc.) before the conftest_helpers star import |
| `smoke_command.py:45` | F541 | Change `print(f"[smoke] ...")` → `print("[smoke] ...")` |

---

## 5. Arch test — prevent recurrence

Add a new file `shell/tests/platform/architecture/test_lint_pass.py`:

```python
"""Verify the codebase passes ruff linting."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

SHELL_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def test_ruff_check_passes() -> None:
    """Fail if ruff check finds any violations."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(SHELL_ROOT / "shell")],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        msg = f"ruff check failed with {result.returncode} errors"
        raise AssertionError(msg)
```

This runs `ruff check shell/` as a pytest test. Any lint regression = red CI.

---

## Order of execution

```
1. C3 (infrastructure_container F821)           — dependency: none
2. C1 (in_memory_unit_of_work E402)              — dependency: none
3. D3 (TC004 — move imports OUT of TYPE_CHECKING) — dependency: none
4. D2 (TC003 — stdlib to TYPE_CHECKING)          — dependency: none
5. D1 (TC002 — 80 files, bulk)                  — dependency: none, but LARGEST
6. 2a (graph_node_execution_run_handler logic)   — dependency: understand existing patterns (done)
7. 2b+2c (F841/F401 - easy removals)            — dependency: after TC reshuffling
8. 4 (one-off fixes)                             — dependency: none
9. `ruff check --fix --unsafe-fixes shell/`      — cleanup pass
10. 5 (arch test)                                — last step
11. `ruff check shell/`                          — verify: 0 errors
12. `pytest shell/tests/ -x -q`                  — verify: tests pass
```

---

## Summary

| Step | What | Errors killed | Files touched |
|------|------|---------------|--------------|
| 1 | TypeVar relocation | 25 | 1 |
| 2 | Unused vars/imports | ~50 | ~20 |
| 3 | TC restructure | ~200 | ~85 |
| 4 | One-off fixes | ~15 | ~10 |
| 5 | `--unsafe-fixes` | ~24 | auto |
| — | **Total** | **~314 → 0** | **~100** |
| — | Arch test | prevention | 1 new |
