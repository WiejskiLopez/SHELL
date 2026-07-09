from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.framework.project.project.api.controller import ProjectController

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_controller() -> ProjectController:
    return ProjectController()


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    controller: ProjectController = Depends(get_project_controller),
) -> dict:
    return await controller.get_project(project_id)
