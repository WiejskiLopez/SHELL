from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
    from shell.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
        ProjectSkillId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True, kw_only=True)
class ProjectSkillCreatedEvent(DomainEvent):
    skill_id: ProjectSkillId
    project_id: ProjectId

    @classmethod
    def now(
        cls,
        *,
        skill_id: ProjectSkillId,
        project_id: ProjectId,
        now: CreatedAt,
    ) -> ProjectSkillCreatedEvent:
        return cls(
            occurred_at=now,
            skill_id=skill_id,
            project_id=project_id,
        )
