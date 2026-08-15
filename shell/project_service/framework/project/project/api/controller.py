from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.models.page import Page
from shell.project_service.application.project.project.commands.create_project_command import (
    CreateProjectCommand,
)
from shell.project_service.application.project.project.commands.delete_project_command import (
    DeleteProjectCommand,
)
from shell.project_service.application.project.project.commands.update_project_command import (
    UpdateProjectCommand,
)
from shell.project_service.application.project.project.queries.get_project_by_id_query import (
    GetProjectByIdQuery,
)
from shell.project_service.application.project.project.queries.list_projects_query import (
    ListProjectsQuery,
)
from shell.project_service.framework.project.project.api.create_project_request import (
    CreateProjectRequest as ApiCreateProjectRequest,
)
from shell.project_service.framework.project.project.api.create_project_response import (
    CreateProjectResponse as ApiCreateProjectResponse,
)
from shell.project_service.framework.project.project.api.project_response import (
    ProjectResponse as ApiProjectResponse,
)
from shell.project_service.framework.project.project.api.update_project_request import (
    UpdateProjectRequest as ApiUpdateProjectRequest,
)

if TYPE_CHECKING:
    from shell.project_service.application.project.project.dto.project import ProjectDto


def _dto_to_response(dto: ProjectDto) -> ApiProjectResponse:
    return ApiProjectResponse(
        id=dto.id,
        name=dto.name,
        repo_url=dto.repo_url,
        status=dto.status,
        created_at=dto.created_at,
        updated_at=dto.updated_at,
        deleted_at=dto.deleted_at,
    )


class ProjectController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
    ) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def list_projects(self, page: int = 1, page_size: int = 100) -> Page[ApiProjectResponse]:
        dtos, total = await self._query_bus.dispatch(
            ListProjectsQuery(page=page, page_size=page_size)
        )
        items = [_dto_to_response(d) for d in dtos]
        has_more = (page * page_size) < total
        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    async def get_project(self, project_id: str) -> ApiProjectResponse:
        result = await self._query_bus.dispatch(GetProjectByIdQuery(project_id=project_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        return ApiProjectResponse(
            id=result.id,
            name=result.name,
            repo_url=result.repo_url,
            status=result.status,
            created_at=result.created_at,
            updated_at=result.updated_at,
            deleted_at=result.deleted_at,
        )

    async def create_project(self, body: ApiCreateProjectRequest) -> ApiCreateProjectResponse:
        project_id = await self._command_bus.dispatch(
            CreateProjectCommand(name=body.name, repo_url=body.repo_url)
        )
        return ApiCreateProjectResponse(id=str(project_id))

    async def update_project(self, project_id: str, body: ApiUpdateProjectRequest) -> None:
        try:
            await self._command_bus.dispatch(
                UpdateProjectCommand(
                    project_id=project_id,
                    name=body.name,
                    repo_url=body.repo_url,
                )
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_project(self, project_id: str) -> None:
        try:
            await self._command_bus.dispatch(DeleteProjectCommand(project_id=project_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
