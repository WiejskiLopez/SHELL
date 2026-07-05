from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.project.aggregates.project_skill.project_skill import ProjectSkill
from shell.domain.project.aggregates.project_skill.repositories.project_skill_repository import (
    ProjectSkillRepository,
)
from shell.domain.project.value_objects.project_skill_id import ProjectSkillId
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.project.value_objects.project_id import ProjectId


class InMemoryProjectSkillRepository(
    InMemoryRepository[ProjectSkill, ProjectSkillId], ProjectSkillRepository
):
    async def get_by_project_id(self, project_id: ProjectId) -> list[ProjectSkill]:
        return [
            skill for skill in self._store.values() if skill.project_id == project_id
        ]
