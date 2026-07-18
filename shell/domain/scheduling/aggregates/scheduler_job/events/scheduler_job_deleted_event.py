from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_job.value_objects.scheduler_job_id import (
        SchedulerJobId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class SchedulerJobDeletedEvent(DomainEvent):
    scheduler_job_id: SchedulerJobId

    @classmethod
    def now(cls, scheduler_job_id: SchedulerJobId, now: CreatedAt) -> SchedulerJobDeletedEvent:
        return cls(occurred_at=now, scheduler_job_id=scheduler_job_id)
