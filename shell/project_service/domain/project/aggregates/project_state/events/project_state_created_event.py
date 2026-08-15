from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
        ProjectId,
    )
    from shell.project_service.domain.project.aggregates.project_state.value_objects.project_state_id import (
        ProjectStateId,
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectStateCreatedEvent(DomainEvent):
    project_id: ProjectId
    project_state_id: ProjectStateId

    @classmethod
    def now(
        cls,
        *,
        project_id: ProjectId,
        project_state_id: ProjectStateId,
        now: OccurredAt,
    ) -> ProjectStateCreatedEvent:
        return cls(
            occurred_at=now,
            project_id=project_id,
            project_state_id=project_state_id,
        )
