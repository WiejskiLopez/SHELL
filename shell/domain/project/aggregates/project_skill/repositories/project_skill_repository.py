from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
    from shell.domain.project.aggregates.project_skill.project_skill import ProjectSkill
    from shell.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
        ProjectSkillId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class ProjectSkillRepository(Protocol):
    async def get_by_id(self, skill_id: ProjectSkillId) -> ProjectSkill | None: ...
    async def get_by_project_id(self, project_id: ProjectId) -> list[ProjectSkill]: ...
    async def save(self, project_skill: ProjectSkill) -> None: ...
    async def delete(self, id: ProjectSkillId) -> None: ...
    async def exists(self, id: ProjectSkillId) -> ExistsResult: ...
