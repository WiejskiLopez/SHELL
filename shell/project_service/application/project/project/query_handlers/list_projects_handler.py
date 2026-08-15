from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.project_service.application.project.project.dto.project import ProjectDto
    from shell.project_service.application.project.project.ports.project_query_service import (
        ProjectQueryService,
    )
    from shell.project_service.application.project.project.queries.list_projects_query import (
        ListProjectsQuery,
    )


class ListProjectsHandler:
    def __init__(self, queries: ProjectQueryService) -> None:
        self._queries = queries

    async def handle(self, query: ListProjectsQuery) -> tuple[list[ProjectDto], int]:
        return await self._queries.list_all(page=query.page, page_size=query.page_size)
