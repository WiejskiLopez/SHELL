from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.repositories.scheduler_job_repository import (
    SchedulerJobRepository,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
    SchedulerJobId,
)

if TYPE_CHECKING:
    from shell.platform.application.ports.unit_of_work import UnitOfWork
    from shell.platform.domain.ports.time import Clock
    from shell.scheduling_service.application.scheduling.scheduler_job.commands.change_scheduler_job_command import (
        ChangeSchedulerJobCommand,
    )


class SchedulerJobNotFoundError(Exception):
    pass


class ChangeSchedulerJobHandler:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._unit_of_work = unit_of_work
        self._clock = clock

    async def handle(self, command: ChangeSchedulerJobCommand) -> None:
        job_id = SchedulerJobId(command.scheduler_job_id)
        async with self._unit_of_work as unit_of_work:
            job = await unit_of_work.repository(SchedulerJobRepository).get_by_id(job_id)
            if job is None:
                raise SchedulerJobNotFoundError(
                    f"SchedulerJob '{command.scheduler_job_id}' not found"
                )
            now = ChangedAt.from_datetime(self._clock.now())
            job.change(now)
            await unit_of_work.save(SchedulerJobRepository, job)
