from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
        SchedulerExecutionId,
    )

    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class SchedulerJobDeletedEvent(DomainEvent):
    schedulerjob_id: SchedulerExecutionId

    @classmethod
    def now(cls, schedulerjob_id: SchedulerExecutionId, now: CreatedAt) -> SchedulerJobDeletedEvent:
        return cls(occurred_at=now, schedulerjob_id=schedulerjob_id)
