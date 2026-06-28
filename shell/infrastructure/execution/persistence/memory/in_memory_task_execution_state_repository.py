from __future__ import annotations

import copy

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
    TaskExecutionStateId,
)
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryTaskExecutionStateRepository(InMemoryRepository[TaskExecutionState, TaskExecutionStateId], TaskExecutionStateRepository):

    async def get_latest_by_task_id(
        self,
        task_execution_id: TaskExecutionId,
        direction: StateDirection | None = None,
    ) -> TaskExecutionState | None:
        latest: TaskExecutionState | None = None
        for item in self._store.values():
            if item.task_execution_id == task_execution_id:
                if direction is not None and item.direction != direction:
                    continue
                if latest is None or item.created_at.value > latest.created_at.value:
                    latest = item
        return copy.deepcopy(latest) if latest is not None else None

    async def save(self, payload: TaskExecutionState) -> None:
        existing = await self.get_latest_by_task_id(payload.task_execution_id, direction=payload.direction)
        if existing is not None:
            existing.supersede()
        self._store[payload.id.value] = copy.deepcopy(payload)

    async def exists(self, id_: TaskExecutionStateId) -> ExistsResult:
        from shell.domain.platform.value_objects.exists_result import ExistsResult

        return ExistsResult(id_.value in self._store)
