from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell.application.project.project.ports.project_query_service import (
    ProjectQueryService,
)
from shell.framework.project.project.api.controller import ProjectController
from shell.framework.project.project.api.create_project_request import (
    CreateProjectRequest,
)
from shell.framework.project.project.api.create_project_response import (
    CreateProjectResponse,
)
from shell.framework.project.project.api.project_response import (
    ProjectResponse,
)
from shell.framework.project.project.api.update_project_request import (
    UpdateProjectRequest,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_controller(
    container: CoreContainer = Depends(get_core_container),
) -> ProjectController:
    try:
        _project_query_service: ProjectQueryService = container.infra.project_query_service
    except Exception:
        raise HTTPException(
            status_code=501, detail="Project query service not implemented"
        ) from None
    command_bus: CommandBus = container.app.buses.command_bus
    return ProjectController(command_bus, _project_query_service)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    controller: ProjectController = Depends(get_project_controller),
) -> ProjectResponse:
    return await controller.get_project(project_id)


@router.post("/", response_model=CreateProjectResponse, status_code=201)
async def create_project(
    body: CreateProjectRequest,
    controller: ProjectController = Depends(get_project_controller),
) -> CreateProjectResponse:
    return await controller.create_project(body)


@router.put("/{project_id}", status_code=204)
async def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    controller: ProjectController = Depends(get_project_controller),
) -> None:
    await controller.update_project(project_id, body)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: str,
    controller: ProjectController = Depends(get_project_controller),
) -> None:
    await controller.delete_project(project_id)
