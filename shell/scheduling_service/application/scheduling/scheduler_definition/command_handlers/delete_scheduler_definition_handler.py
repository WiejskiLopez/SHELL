from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.repositories.scheduler_definition_repository import (
    SchedulerDefinitionRepository,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock
    from shell.scheduling_service.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
        DeleteSchedulerDefinitionCommand,
    )


class SchedulerDefinitionNotFoundError(Exception):
    pass


class DeleteSchedulerDefinitionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: DeleteSchedulerDefinitionCommand) -> None:
        definition_id = SchedulerDefinitionId(command.scheduler_definition_id)
        async with self._unit_of_work as unit_of_work:
            definition = await unit_of_work.repository(SchedulerDefinitionRepository).get_by_id(
                definition_id
            )
            if definition is None:
                raise SchedulerDefinitionNotFoundError(
                    f"SchedulerDefinition '{command.scheduler_definition_id}' not found"
                )
            now = DeletedAt.from_datetime(self._clock.now())
            definition.delete(now)
            await unit_of_work.save(SchedulerDefinitionRepository, definition)
