from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
    from shell.domain.execution.aggregates.task_execution_state_input.task_execution_state_input import (
        TaskExecutionStateInput,
    )


class TaskExecutionStateInputRepository(Protocol):
    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionStateInput | None: ...

    async def save(self, payload: TaskExecutionStateInput) -> None: ...
