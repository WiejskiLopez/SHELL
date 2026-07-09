from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.project.project.dto.project import ProjectDto
    from shell.application.project.project.ports.project_query_service import ProjectQueryService
    from shell.application.project.project.queries.get_project_by_id_query import (
        GetProjectByIdQuery,
    )


class GetProjectByIdHandler:
    def __init__(self, queries: ProjectQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetProjectByIdQuery) -> ProjectDto | None:
        return await self._queries.get_by_id(query.project_id)
