from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
    from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
        ProjectStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectStateChangedEvent(DomainEvent):
    project_id: ProjectId
    project_state_id: ProjectStateId

    @classmethod
    def now(
        cls,
        *,
        project_id: ProjectId,
        project_state_id: ProjectStateId,
        now: CreatedAt,
    ) -> ProjectStateChangedEvent:
        return cls(
            occurred_at=now,
            project_id=project_id,
            project_state_id=project_state_id,
        )
