from __future__ import annotations

from fastapi import HTTPException


class ProjectController:
    async def get_project(self, project_id: str) -> dict:
        raise HTTPException(status_code=501, detail="Project ACL not implemented")
