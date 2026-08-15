from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.project_service.application.project.project.dto.project import ProjectDto


class ProjectQueryService(Protocol):
    async def get_by_id(self, project_id: str) -> ProjectDto | None: ...

    async def list_all(
        self, *, page: int = 1, page_size: int = 100
    ) -> tuple[list[ProjectDto], int]: ...
