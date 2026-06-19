from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_input_payload import (
        TaskExecutionInputPayload,
    )
    from shell.domain.platform.value_objects.ids import TaskExecutionId


class TaskExecutionInputPayloadRepository(Protocol):
    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionInputPayload | None: ...

    async def save(self, payload: TaskExecutionInputPayload) -> None: ...
