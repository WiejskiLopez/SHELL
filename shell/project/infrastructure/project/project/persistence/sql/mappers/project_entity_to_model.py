"""SQL ORM model <-> domain entity mappers for Project aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.project.infrastructure.project.project.persistence.sql.models.project import ProjectModel

if TYPE_CHECKING:
    from shell.project.domain.project.aggregates.project.project import Project


def project_entity_to_model(entity: Project) -> ProjectModel:
    return ProjectModel(
        id=entity.id.value,
        name=entity.name.value,
        repo_url=entity.repo_url.value,
        status=entity.status.value,
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value,
        deleted_at=entity.deleted_at.value,
    )
