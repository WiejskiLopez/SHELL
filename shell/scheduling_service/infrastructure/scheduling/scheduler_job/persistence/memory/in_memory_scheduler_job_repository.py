from __future__ import annotations

from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.scheduler_job import (
    SchedulerJob,
)
from shell.scheduling_service.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
    SchedulerJobId,
)


class InMemorySchedulerJobRepository(InMemoryRepository[SchedulerJob, SchedulerJobId]):
    pass
