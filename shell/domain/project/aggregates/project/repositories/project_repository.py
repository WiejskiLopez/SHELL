from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from shell.domain.project.aggregates.project.project import Project
    from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId


class ProjectRepository(Protocol):
    async def get_by_id(self, project_id: ProjectId) -> Project | None: ...
    async def save(self, project: Project) -> None: ...
    async def delete(self, id: ProjectId) -> None: ...
    async def exists(self, id: ProjectId) -> ExistsResult: ...
