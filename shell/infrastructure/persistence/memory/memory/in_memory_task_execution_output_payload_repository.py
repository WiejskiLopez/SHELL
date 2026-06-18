from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.repositories.task_execution_output_payload_repository import (
    TaskExecutionOutputPayloadRepository,
)
from shell.domain.value_objects.ids import TaskExecutionId

if TYPE_CHECKING:
    from shell.domain.aggregates.task_execution_output_payload import (
        TaskExecutionOutputPayload,
    )


class InMemoryTaskExecutionOutputPayloadRepository(TaskExecutionOutputPayloadRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecutionOutputPayload] = {}

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionOutputPayload | None:
        for payload in self._store.values():
            if payload.task_execution_id == task_execution_id and payload.is_current:
                return payload
        return None

    async def save(self, payload: TaskExecutionOutputPayload) -> None:
        self._store[payload.id.value] = payload
