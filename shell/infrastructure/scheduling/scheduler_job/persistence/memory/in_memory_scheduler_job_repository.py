from __future__ import annotations

from shell.domain.scheduling.aggregates.scheduler_job.scheduler_job import SchedulerJob
from shell.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
    SchedulerJobId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemorySchedulerJobRepository(InMemoryRepository[SchedulerJob, SchedulerJobId]):
    pass
