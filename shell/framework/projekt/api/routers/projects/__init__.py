from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as _Request

if TYPE_CHECKING:
    from shell.bootstrap.platform.container.core_container import CoreContainer
    from shell.domain.projekt.ports.project_acl import ProjectACL

router = APIRouter(prefix="/projects", tags=["projects"])


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    container: CoreContainer = Depends(get_core_container),
) -> dict:
    _project_acl: ProjectACL | None = getattr(container.infra, "project_acl_factory", None)  # type: ignore[attr-defined]
    if _project_acl is None:
        raise HTTPException(status_code=501, detail="Project ACL not implemented")
    result = await _project_acl.get_project(project_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return {"id": project_id, "project": str(result)}
