from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.scheduling.aggregates.scheduler_definition.value_objects.scheduler_definition_id import (
        SchedulerDefinitionId,
    )

    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class SchedulerDefinitionDeletedEvent(DomainEvent):
    schedulerdefinition_id: SchedulerDefinitionId

    @classmethod
    def now(cls, schedulerdefinition_id: SchedulerDefinitionId, now: CreatedAt) -> SchedulerDefinitionDeletedEvent:
        return cls(occurred_at=now, schedulerdefinition_id=schedulerdefinition_id)
