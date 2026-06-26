from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution_state.repositories.task_execution_state_repository import (
    TaskExecutionStateRepository,
)
from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
    TaskExecutionStateId,
)
from shell.domain.execution.value_objects.state_kind import StateKind

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )


class InMemoryTaskExecutionStateRepository(TaskExecutionStateRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecutionState] = {}

    async def get_latest_by_task_id(
        self,
        task_execution_id: TaskExecutionId,
        kind: StateKind | None = None,
    ) -> TaskExecutionState | None:
        latest: TaskExecutionState | None = None
        for item in self._store.values():
            if item.task_execution_id == task_execution_id:
                if kind is not None and item.kind != kind:
                    continue
                if latest is None or item.created_at > latest.created_at:
                    latest = item
        return copy.deepcopy(latest) if latest is not None else None

    async def save(self, payload: TaskExecutionState) -> None:
        existing = await self.get_latest_by_task_id(payload.task_execution_id, kind=payload.kind)
        if existing is not None:
            existing.supersede()
        self._store[payload.id.value] = copy.deepcopy(payload)

    async def delete(self, id_: TaskExecutionStateId) -> None:
        self._store.pop(id_.value, None)

    async def exists(self, id_: TaskExecutionStateId) -> bool:
        return id_.value in self._store
