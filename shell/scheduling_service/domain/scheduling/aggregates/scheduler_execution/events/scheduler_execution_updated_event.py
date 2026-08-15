from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.scheduling_service.domain.scheduling.aggregates.scheduler_execution.value_objects.scheduler_execution_id import (
        SchedulerExecutionId,
    )


@dataclass(frozen=True, slots=True)
class SchedulerExecutionUpdatedEvent(DomainEvent):
    scheduler_execution_id: SchedulerExecutionId

    @classmethod
    def now(
        cls, scheduler_execution_id: SchedulerExecutionId, now: OccurredAt
    ) -> SchedulerExecutionUpdatedEvent:
        return cls(occurred_at=now, scheduler_execution_id=scheduler_execution_id)
