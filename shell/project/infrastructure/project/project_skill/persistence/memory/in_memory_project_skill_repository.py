from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
from shell.project.domain.project.aggregates.project_skill.project_skill import ProjectSkill
from shell.project.domain.project.aggregates.project_skill.repositories.project_skill_repository import (
    ProjectSkillRepository,
)
from shell.project.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
    ProjectSkillId,
)

if TYPE_CHECKING:
    from shell.project.domain.project.aggregates.project.value_objects.project_id import ProjectId


class InMemoryProjectSkillRepository(
    InMemoryRepository[ProjectSkill, ProjectSkillId], ProjectSkillRepository
):
    async def get_by_project_id(self, project_id: ProjectId) -> list[ProjectSkill]:
        return [skill for skill in self._store.values() if skill.project_id == project_id]
