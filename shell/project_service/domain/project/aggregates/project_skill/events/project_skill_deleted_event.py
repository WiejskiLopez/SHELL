from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.project_service.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
        ProjectSkillId,
    )


@dataclass(frozen=True, slots=True)
class ProjectSkillDeletedEvent(DomainEvent):
    project_skill_id: ProjectSkillId

    @classmethod
    def now(cls, project_skill_id: ProjectSkillId, now: OccurredAt) -> ProjectSkillDeletedEvent:
        return cls(occurred_at=now, project_skill_id=project_skill_id)
