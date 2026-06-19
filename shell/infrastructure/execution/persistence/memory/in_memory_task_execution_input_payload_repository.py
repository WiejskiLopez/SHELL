from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.repositories.task_execution_input_payload_repository import (
    TaskExecutionInputPayloadRepository,
)
from shell.domain.execution.value_objects.ids import TaskExecutionId

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_input_payload import (
        TaskExecutionInputPayload,
    )


class InMemoryTaskExecutionInputPayloadRepository(TaskExecutionInputPayloadRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecutionInputPayload] = {}

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionInputPayload | None:
        for payload in self._store.values():
            if payload.task_execution_id == task_execution_id and payload.is_current:
                return payload
        return None

    async def save(self, payload: TaskExecutionInputPayload) -> None:
        self._store[payload.id.value] = payload
