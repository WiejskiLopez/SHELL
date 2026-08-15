from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.repositories.scheduler_execution_repository import (
    SchedulerExecutionRepository,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.scheduler_execution import (
    SchedulerExecution,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
    SchedulerExecutionId,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.identity import IdGenerator
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock
    from shell.scheduling_service.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
        CreateSchedulerExecutionCommand,
    )


class SchedulerExecutionNotFoundError(Exception):
    pass


class CreateSchedulerExecutionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateSchedulerExecutionCommand) -> str:
        now = CreatedAt.from_datetime(self._clock.now())
        execution_id = self._id_generator.new_id(SchedulerExecutionId)
        definition_id = SchedulerDefinitionId(command.scheduler_definition_id)

        execution = SchedulerExecution.create(
            id_=execution_id,
            now=now,
            scheduler_definition_id=definition_id,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(SchedulerExecutionRepository, execution)
        return execution_id.value
