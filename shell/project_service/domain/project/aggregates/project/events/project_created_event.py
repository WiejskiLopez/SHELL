from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
        ProjectId,
    )


@dataclass(frozen=True, slots=True)
class ProjectCreatedEvent(DomainEvent):
    project_id: ProjectId

    @classmethod
    def now(cls, project_id: ProjectId, now: OccurredAt) -> ProjectCreatedEvent:
        return cls(occurred_at=now, project_id=project_id)
