from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project_skill.value_objects.ProjectSkillId import ProjectSkillId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class ProjectSkillUpdatedEvent(DomainEvent):
    projectskill_id: ProjectSkillId

    @classmethod
    def now(cls, projectskill_id: ProjectSkillId, now: CreatedAt) -> "ProjectSkillUpdatedEvent":
        return cls(occurred_at=now, projectskill_id=projectskill_id)
