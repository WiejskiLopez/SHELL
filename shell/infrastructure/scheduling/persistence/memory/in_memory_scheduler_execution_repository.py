from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId


class InMemorySchedulerExecutionRepository:
    def __init__(self) -> None:
        self._store: dict[str, SchedulerExecution] = {}

    async def get_by_id(
        self, id: SchedulerExecutionId
    ) -> SchedulerExecution | None:
        return self._store.get(id.value)

    async def get_by_action_ref(
        self, action_ref: str
    ) -> list[SchedulerExecution]:
        return [
            e for e in self._store.values() if e.action_ref == action_ref
        ]

    async def count_by_definition_and_status(
        self, definition_id: str, status: str
    ) -> int:
        return sum(
            1
            for e in self._store.values()
            if e.scheduler_definition_id.value == definition_id
            and e.status.value == status
        )

    async def save(self, execution: SchedulerExecution) -> None:
        self._store[execution.id.value] = execution
