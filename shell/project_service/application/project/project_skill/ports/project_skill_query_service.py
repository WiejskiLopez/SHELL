from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.project_service.application.project.project_skill.dto.project_skill import (
        ProjectSkillDto,
    )


class ProjectSkillQueryService(Protocol):
    async def get_by_id(self, project_skill_id: str) -> ProjectSkillDto | None: ...
