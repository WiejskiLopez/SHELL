from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.project.ports.project_acl import ProjectACL

if TYPE_CHECKING:
    import httpx

    from shell.domain.project.aggregates.project.project import Project
    from shell.domain.project.value_objects.project_id import ProjectId


class ProjectAclHttpAdapter(ProjectACL):
    def __init__(self, client: httpx.AsyncClient) -> None:
        self._client = client

    async def get_project(self, project_id: ProjectId) -> Project:
        response = await self._client.get(f"/api/v1/projects/{project_id}")
        if response.status_code == 501:
            raise NotImplementedError("Project BC REST API not fully implemented yet")
        response.raise_for_status()
        data = response.json()
        raise NotImplementedError(
            f"Project deserialization from JSON not implemented yet. Got: {data}"
        )
