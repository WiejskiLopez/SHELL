from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.framework.project.project.api.controller import ProjectController
from shell.framework.project.project.api.project_response import (
    ProjectResponse,  # noqa: TC001 — FastAPI needs it at runtime for response_model
)

router = APIRouter(prefix="/projects", tags=["Projects"])


def get_project_controller() -> ProjectController:
    return ProjectController()


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    controller: ProjectController = Depends(get_project_controller),
) -> ProjectResponse:
    return await controller.get_project(project_id)
