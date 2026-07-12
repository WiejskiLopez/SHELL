from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class ProjectUpdatedEvent(DomainEvent):
    project_id: ProjectId

    @classmethod
    def now(cls, project_id: ProjectId, now: CreatedAt) -> ProjectUpdatedEvent:
        return cls(occurred_at=now, project_id=project_id)
