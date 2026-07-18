from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_execution.value_objects.SchedulerExecutionId import (
        SchedulerExecutionId,
    )

    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class SchedulerExecutionUpdatedEvent(DomainEvent):
    schedulerexecution_id: SchedulerExecutionId

    @classmethod
    def now(cls, schedulerexecution_id: SchedulerExecutionId, now: CreatedAt) -> SchedulerExecutionUpdatedEvent:
        return cls(occurred_at=now, schedulerexecution_id=schedulerexecution_id)
