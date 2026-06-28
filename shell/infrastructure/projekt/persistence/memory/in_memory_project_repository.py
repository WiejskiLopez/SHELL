from __future__ import annotations

from shell.domain.projekt.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.domain.projekt.value_objects.project_id import ProjectId
from shell.domain.projekt.aggregates.project.project import Project
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryProjectRepository(InMemoryRepository[Project, ProjectId], ProjectRepository):
    pass
