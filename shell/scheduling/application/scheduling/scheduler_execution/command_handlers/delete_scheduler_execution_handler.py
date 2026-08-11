from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.repositories.scheduler_execution_repository import (
    SchedulerExecutionRepository,
)
from shell.scheduling.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock
    from shell.scheduling.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
        DeleteSchedulerExecutionCommand,
    )


class SchedulerExecutionNotFoundError(Exception):
    pass


class DeleteSchedulerExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: DeleteSchedulerExecutionCommand) -> None:
        execution_id = SchedulerExecutionId(command.scheduler_execution_id)
        async with self._unit_of_work as unit_of_work:
            execution = await unit_of_work.repository(SchedulerExecutionRepository).get_by_id(
                execution_id
            )
            if execution is None:
                raise SchedulerExecutionNotFoundError(
                    f"SchedulerExecution '{command.scheduler_execution_id}' not found"
                )
            now = DeletedAt.from_datetime(self._clock.now())
            execution._delete(now)
            await unit_of_work.save(SchedulerExecutionRepository, execution)
