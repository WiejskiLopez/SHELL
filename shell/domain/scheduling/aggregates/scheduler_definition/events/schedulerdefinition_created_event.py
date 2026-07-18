from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.schedulerdefinition.aggregates.schedulerdefinition.value_objects.SchedulerDefinitionId import SchedulerDefinitionId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class SchedulerDefinitionCreatedEvent(DomainEvent):
    schedulerdefinition_id: SchedulerDefinitionId

    @classmethod
    def now(cls, schedulerdefinition_id: SchedulerDefinitionId, now: CreatedAt) -> "SchedulerDefinitionCreatedEvent":
        return cls(occurred_at=now, schedulerdefinition_id=schedulerdefinition_id)
