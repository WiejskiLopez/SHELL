from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.state_direction import StateDirection
    from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
        ProjectStateId,
    )
    from shell.domain.project.value_objects.project_id import ProjectId


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectStateChangedEvent(DomainEvent):
    project_id: ProjectId
    project_state_id: ProjectStateId
    direction: StateDirection
    key: str
    old_value: object | None
    new_value: object | None

    @classmethod
    def now(
        cls,
        *,
        project_id: ProjectId,
        project_state_id: ProjectStateId,
        direction: StateDirection,
        key: str,
        old_value: object | None,
        new_value: object | None,
        now: CreatedAt,
    ) -> ProjectStateChangedEvent:
        return cls(
            occurred_at=now,
            project_id=project_id,
            project_state_id=project_state_id,
            direction=direction,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )
