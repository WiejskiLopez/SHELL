from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project_state.value_objects.ProjectStateId import ProjectStateId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class ProjectStateDeletedEvent(DomainEvent):
    projectstate_id: ProjectStateId

    @classmethod
    def now(cls, projectstate_id: ProjectStateId, now: CreatedAt) -> "ProjectStateDeletedEvent":
        return cls(occurred_at=now, projectstate_id=projectstate_id)
