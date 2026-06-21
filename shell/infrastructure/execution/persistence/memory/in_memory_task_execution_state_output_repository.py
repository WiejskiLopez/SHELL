from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.task_execution_state_output.ports.task_execution_state_output_repository import (
    TaskExecutionStateOutputRepository,
)
from shell.domain.execution.value_objects.ids import (
    TaskExecutionId,  # noqa: TC002 — TaskExecutionId używany w konstruktorach w repozytorium
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state_output.task_execution_state_output import (
        TaskExecutionStateOutput,
    )


class InMemoryTaskExecutionStateOutputRepository(TaskExecutionStateOutputRepository):
    def __init__(self) -> None:
        self._store: dict[str, TaskExecutionStateOutput] = {}

    async def get_latest_by_task_id(
        self, task_execution_id: TaskExecutionId
    ) -> TaskExecutionStateOutput | None:
        for payload in self._store.values():
            if payload.task_execution_id == task_execution_id and payload.is_current:
                return payload
        return None

    async def save(self, payload: TaskExecutionStateOutput) -> None:
        self._store[payload.id.value] = payload
