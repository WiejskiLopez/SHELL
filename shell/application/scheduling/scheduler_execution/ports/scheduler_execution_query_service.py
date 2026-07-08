from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.scheduling.scheduler_execution.dto.scheduler_execution import (
        SchedulerExecutionDto,
    )


class SchedulerExecutionQueryService(Protocol):
    async def get_by_id(
        self, scheduler_execution_id: str
    ) -> SchedulerExecutionDto | None: ...
