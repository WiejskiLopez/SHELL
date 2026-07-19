from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.scheduling.aggregates.scheduler_definition.repositories.scheduler_definition_repository import (
    SchedulerDefinitionRepository,
)
from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.platform.domain.value_objects.updated_at import UpdatedAt

if TYPE_CHECKING:
    from shell.application.scheduling.scheduler_definition.commands.update_scheduler_definition_command import (
        UpdateSchedulerDefinitionCommand,
    )
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock


class SchedulerDefinitionNotFoundError(Exception):
    pass


class UpdateSchedulerDefinitionHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: UpdateSchedulerDefinitionCommand) -> None:
        definition_id = SchedulerDefinitionId(command.scheduler_definition_id)
        async with self._unit_of_work as unit_of_work:
            definition = await unit_of_work.repository(SchedulerDefinitionRepository).get_by_id(
                definition_id
            )
            if definition is None:
                raise SchedulerDefinitionNotFoundError(
                    f"SchedulerDefinition '{command.scheduler_definition_id}' not found"
                )
            now = UpdatedAt.from_datetime(self._clock.now())
            definition.update(now)
            await unit_of_work.save(SchedulerDefinitionRepository, definition)
