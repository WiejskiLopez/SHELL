from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.projekt.value_objects.project_id import ProjectId
    from shell.domain.projekt.value_objects.project_skill_payload import ProjectSkillPayload


@dataclass(frozen=True, slots=True)
class ProjectStateInput:
    project_id: ProjectId
    payload: ProjectSkillPayload
    created_at: CreatedAt
