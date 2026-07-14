from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )
    from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
        TaskExecutionStateId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class TaskExecutionStateRepository(Protocol):
    async def get_by_id(self, id: TaskExecutionStateId) -> TaskExecutionState | None: ...

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionState | None: ...

    async def save(self, state: TaskExecutionState) -> None: ...
    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...
