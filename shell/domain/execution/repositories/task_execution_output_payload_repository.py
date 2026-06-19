from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_output_payload import (
        TaskExecutionOutputPayload,
    )
    from shell.domain.execution.value_objects.ids import TaskExecutionId


class TaskExecutionOutputPayloadRepository(Protocol):
    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionOutputPayload | None: ...

    async def save(self, payload: TaskExecutionOutputPayload) -> None: ...
