from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

if TYPE_CHECKING:
    from shell.framework.project.project.api.project_response import ProjectResponse


class ProjectController:
    async def get_project(self, project_id: str) -> ProjectResponse:
        raise HTTPException(status_code=501, detail="Project ACL not implemented")
