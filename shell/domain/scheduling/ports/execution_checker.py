from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition import (
        SchedulerDefinition,
    )
    from shell.domain.scheduling.aggregates.scheduler_execution import (
        SchedulerExecution,
    )


class ExecutionChecker(Protocol):
    async def can_execute(
        self,
        *,
        definition: SchedulerDefinition,
        execution: SchedulerExecution,
    ) -> bool:
        ...
