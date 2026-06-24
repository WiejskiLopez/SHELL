from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.projekt.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.domain.projekt.value_objects.project_id import ProjectId

if TYPE_CHECKING:
    from shell.domain.projekt.aggregates.project.project import Project


class InMemoryProjectRepository(ProjectRepository):
    def __init__(self) -> None:
        self._store: dict[str, Project] = {}

    async def get_by_id(self, project_id: ProjectId) -> Project | None:
        project = self._store.get(project_id.value)
        return copy.deepcopy(project) if project is not None else None

    async def save(self, project: Project) -> None:
        self._store[project.id.value] = copy.deepcopy(project)
