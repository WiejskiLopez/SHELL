from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )


class InMemoryTaskExecutionStateOutputRepository(TaskExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecutionState] = {}

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionState | None:
        for payload in self._store.values():
            if payload.task_execution_id == task_execution_id and payload.is_current.value:
                return payload
        return None

    async def save(self, payload: TaskExecutionState) -> None:
        self._store[payload.id.value] = payload

    async def delete(self, id: object) -> None:
        ...

    async def exists(self, id: object) -> bool:
        ...
