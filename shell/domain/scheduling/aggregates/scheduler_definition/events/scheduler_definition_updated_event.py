from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class SchedulerDefinitionUpdatedEvent(DomainEvent):
    scheduler_definition_id: SchedulerDefinitionId

    @classmethod
    def now(
        cls, scheduler_definition_id: SchedulerDefinitionId, now: OccurredAt
    ) -> SchedulerDefinitionUpdatedEvent:
        return cls(occurred_at=now, scheduler_definition_id=scheduler_definition_id)
