from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.projekt.aggregates.project.project import Project
    from shell.domain.projekt.value_objects.project_id import ProjectId


class ProjectACL(Protocol):
    async def get_project(self, project_id: ProjectId) -> Project: ...
