from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.domain.project.value_objects.project_id import ProjectId

if TYPE_CHECKING:
    from shell.domain.project.ports.project_acl import ProjectACL


class ProjectController:
    __slots__ = ("_project_acl",)

    def __init__(self, project_acl: ProjectACL) -> None:
        self._project_acl = project_acl

    async def get_project(self, project_id: str) -> dict:
        result = await self._project_acl.get_project(ProjectId(project_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        return {"id": project_id, "project": str(result)}
