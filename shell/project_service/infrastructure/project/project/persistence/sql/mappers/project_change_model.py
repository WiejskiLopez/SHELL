"""SQL ORM model <-> domain entity mappers for Project aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.project_service.domain.project.aggregates.project.project import Project
    from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
        ProjectModel,
    )


def project_change_model(model: ProjectModel, entity: Project) -> None:
    model.name = entity.name.value
    model.repo_url = entity.repository_url.value
    model.status = entity.status.value
    model.created_at = entity.created_at.value if entity.created_at else None  # type: ignore[assignment]
    model.changed_at = entity.changed_at.value
    model.deleted_at = entity.deleted_at.value
