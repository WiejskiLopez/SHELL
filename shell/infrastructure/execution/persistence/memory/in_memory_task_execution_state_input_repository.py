from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution_state_input.ports.task_execution_state_input_repository import (
    TaskExecutionStateInputRepository,
)
from shell.domain.execution.value_objects.ids import (
    TaskExecutionId,  # noqa: TC002 — TaskExecutionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state_input.task_execution_state_input import (
        TaskExecutionStateInput,
    )


class InMemoryTaskExecutionStateInputRepository(TaskExecutionStateInputRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecutionStateInput] = {}

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionStateInput | None:
        for payload in self._store.values():
            if payload.task_execution_id == task_execution_id and payload.is_current:
                return payload
        return None

    async def save(self, payload: TaskExecutionStateInput) -> None:
        self._store[payload.id.value] = payload
