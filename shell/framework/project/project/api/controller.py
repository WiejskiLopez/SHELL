from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.project.project.commands.create_project_command import (
    CreateProjectCommand,
)
from shell.application.project.project.commands.delete_project_command import (
    DeleteProjectCommand,
)
from shell.application.project.project.commands.update_project_command import (
    UpdateProjectCommand,
)
from shell.framework.project.project.api.create_project_request import (
    CreateProjectRequest as ApiCreateProjectRequest,
)
from shell.framework.project.project.api.create_project_response import (
    CreateProjectResponse as ApiCreateProjectResponse,
)
from shell.framework.project.project.api.project_response import (
    ProjectResponse as ApiProjectResponse,
)
from shell.framework.project.project.api.update_project_request import (
    UpdateProjectRequest as ApiUpdateProjectRequest,
)
from shell.platform.application.bus.command_bus import CommandBus

if TYPE_CHECKING:
    from shell.application.project.project.ports.project_query_service import (
        ProjectQueryService,
    )


class ProjectController:
    __slots__ = ("_command_bus", "_project_query_service")

    def __init__(
        self,
        command_bus: CommandBus,
        project_query_service: ProjectQueryService,
    ) -> None:
        self._command_bus = command_bus
        self._project_query_service = project_query_service

    async def get_project(self, project_id: str) -> ApiProjectResponse:
        result = await self._project_query_service.get_by_id(project_id)
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
