from __future__ import annotations

from shell.project_service.domain.project.aggregates.project.project import Project
from shell.project_service.domain.project.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
    ProjectId,
)

__all__ = [
    "Project",
    "ProjectId",
    "ProjectRepository",
]
