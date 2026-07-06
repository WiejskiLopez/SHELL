from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from shell.framework.platform.api.dependencies import get_core_container
from shell.framework.project.project.api.controller import ProjectController

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer
    from shell.domain.project.ports.project_acl import ProjectACL

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_controller(
    container: CoreContainer = Depends(get_core_container),
) -> ProjectController:
    _project_acl: ProjectACL | None = getattr(container.infra, "project_acl_factory", None)
    if _project_acl is None:
        raise HTTPException(status_code=501, detail="Project ACL not implemented")
    return ProjectController(_project_acl)


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    controller: ProjectController = Depends(get_project_controller),
) -> dict:
    return await controller.get_project(project_id)
