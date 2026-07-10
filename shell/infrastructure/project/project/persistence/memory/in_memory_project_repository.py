from __future__ import annotations

from shell.domain.project.aggregates.project.project import Project
from shell.domain.project.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemoryProjectRepository(InMemoryRepository[Project, ProjectId], ProjectRepository):
    pass
