from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.types import JsonStr
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
    SchedulerDefinitionId,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.repositories.scheduler_job_repository import (
    SchedulerJobRepository,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
    SchedulerJob,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.batch_size import (
    BatchSize,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.interval_seconds import (
    IntervalSeconds,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.job_name import (
    JobName,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.job_type import (
    JobType,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
    SchedulerJobId,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.persistence.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.identity import IdGenerator
    from shell.platform.domain.ports.time import Clock
    from shell.scheduling_service.application.scheduling.scheduler_job.commands.create_scheduler_job_command import (
        CreateSchedulerJobCommand,
    )


class SchedulerJobNotFoundError(Exception):
    pass


class CreateSchedulerJobHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
        id_generator: IdGenerator,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock
        self._id_generator = id_generator

    async def handle(self, command: CreateSchedulerJobCommand) -> str:
        now = CreatedAt.from_datetime(self._clock.now())
        job_id = self._id_generator.new_id(SchedulerJobId)
        definition_id = SchedulerDefinitionId(command.scheduler_definition_id)

        job = SchedulerJob.create(
            id_=job_id,
            now=now,
            scheduler_definition_id=definition_id,
            name=JobName(command.name),
            job_type=JobType(command.job_type),
            interval_seconds=IntervalSeconds(command.interval_seconds),
            batch_size=BatchSize(command.batch_size),
            config=StateData(value=JsonStr("{}")),
            enabled=command.enabled,
        )
        async with self._unit_of_work as unit_of_work:
            await unit_of_work.save(SchedulerJobRepository, job)
        return job_id.value
