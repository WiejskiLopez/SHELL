from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.repositories.task_execution_repository import (
    TaskExecutionRepository,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )


class InMemoryTaskExecutionStateRepository(TaskExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecutionState] = {}

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionState | None:
        latest: TaskExecutionState | None = None
        for item in self._store.values():
            if item.task_execution_id == task_execution_id:
                if latest is None or item.created_at > latest.created_at:
                    latest = item
        return copy.deepcopy(latest) if latest is not None else None

    async def save(self, payload: TaskExecutionState) -> None:
        self._store[payload.id.value] = copy.deepcopy(payload)

    async def delete(self, id: object) -> None:
        key = str(id)
        self._store.pop(key, None)

    async def exists(self, id: object) -> bool:
        return str(id) in self._store
