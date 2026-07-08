from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.project.project.dto.project import ProjectDto


class ProjectQueryService(Protocol):
    async def get_by_id(self, project_id: str) -> ProjectDto | None: ...
