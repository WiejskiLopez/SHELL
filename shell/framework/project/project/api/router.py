from __future__ import annotations

from fastapi import APIRouter, Depends, Query

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
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container
from shell.platform.framework.api.models.page import Page

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_controller(
    container: CoreContainer = Depends(get_core_container),
) -> ProjectController:
    command_bus: CommandBus = container.app.buses.command_bus
    query_bus: QueryBus = container.app.buses.query_bus
    return ProjectController(command_bus, query_bus)


@router.get("", response_model=Page[ProjectResponse])
async def list_projects(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000, alias="page_size"),
    controller: ProjectController = Depends(get_project_controller),
) -> Page[ProjectResponse]:
    return await controller.list_projects(page=page, page_size=page_size)


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
