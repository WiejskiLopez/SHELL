from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.project.domain.project.aggregates.project_state.value_objects.project_state_id import (
        ProjectStateId,
    )


@dataclass(frozen=True, slots=True)
class ProjectStateUpdatedEvent(DomainEvent):
    project_state_id: ProjectStateId

    @classmethod
    def now(cls, project_state_id: ProjectStateId, now: OccurredAt) -> ProjectStateUpdatedEvent:
        return cls(occurred_at=now, project_state_id=project_state_id)
