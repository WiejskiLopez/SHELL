"""SQL ORM model <-> domain entity mappers for Project aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.project.aggregates.project.project import Project
from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project.value_objects.project_name import ProjectName
from shell.domain.project.aggregates.project.value_objects.project_status import ProjectStatus
from shell.domain.project.aggregates.project.value_objects.repo_url import RepoUrl
from shell.infrastructure.project.project.persistence.sql.models.project import ProjectModel
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def project_update_model(model: ProjectModel, entity: Project) -> None:
    model.name = entity.name.value
    model.repo_url = entity.repo_url.value
    model.status = entity.status.value
    model.created_at = entity.created_at.value if entity.created_at else None  # type: ignore[assignment]
    model.updated_at = entity.updated_at.value if entity.updated_at else None
    model.deleted_at = entity.deleted_at.value if entity.deleted_at else None