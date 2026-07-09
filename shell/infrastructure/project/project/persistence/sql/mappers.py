"""SQL ORM model <-> domain entity mappers for Project aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.project.aggregates.project.project import Project
from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project.value_objects.project_name import ProjectName
from shell.domain.project.aggregates.project.value_objects.project_status import ProjectStatus
from shell.domain.project.aggregates.project.value_objects.repo_url import RepoUrl
from shell.infrastructure.project.project.persistence.sql.models.project import ProjectModel


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def project_model_to_entity(model: ProjectModel) -> Project:
    return Project.restore(
        id=ProjectId(model.id),
        name=ProjectName(model.name),
        repo_url=RepoUrl(model.repo_url),
        status=ProjectStatus(model.status),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at))
        if model.created_at
        else None,
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at))
        if model.updated_at is not None
        else None,
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at))
        if model.deleted_at is not None
        else None,
    )


def project_entity_to_model(entity: Project) -> ProjectModel:
    return ProjectModel(
        id=entity.id.value,
        name=entity.name.value,
        repo_url=entity.repo_url.value,
        status=entity.status.value,
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value if entity.updated_at else None,
        deleted_at=entity.deleted_at.value if entity.deleted_at else None,
    )


def project_update_model(model: ProjectModel, entity: Project) -> None:
    model.name = entity.name.value
    model.repo_url = entity.repo_url.value
    model.status = entity.status.value
    model.created_at = entity.created_at.value if entity.created_at else None  # type: ignore[assignment]
    model.updated_at = entity.updated_at.value if entity.updated_at else None
    model.deleted_at = entity.deleted_at.value if entity.deleted_at else None
