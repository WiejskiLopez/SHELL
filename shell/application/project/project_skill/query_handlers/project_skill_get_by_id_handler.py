from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.project.project_skill.dto.project_skill import ProjectSkillDto
    from shell.application.project.project_skill.ports.project_skill_query_service import (
        ProjectSkillQueryService,
    )
    from shell.application.project.project_skill.queries.project_skill_get_by_id_query import (
        ProjectSkillGetByIdQuery,
    )


class ProjectSkillGetByIdHandler:
    def __init__(self, queries: ProjectSkillQueryService) -> None:
        self._queries = queries

    async def handle(self, query: ProjectSkillGetByIdQuery) -> ProjectSkillDto | None:
        return await self._queries.get_by_id(query.project_skill_id)
