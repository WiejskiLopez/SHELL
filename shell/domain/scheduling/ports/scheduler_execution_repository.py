from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_execution import (
        SchedulerExecution,
    )
    from shell.domain.scheduling.value_objects.ids import SchedulerExecutionId


class SchedulerExecutionRepository(Protocol):
    async def get_by_id(
        self, id: SchedulerExecutionId
    ) -> SchedulerExecution | None:
        ...

    async def get_by_action_ref(
        self, action_ref: str
    ) -> list[SchedulerExecution]:
        ...

    async def count_by_definition_and_status(
        self, scheduler_definition_id: str, status: str
    ) -> int:
        ...

    async def save(self, execution: SchedulerExecution) -> None:
        ...
