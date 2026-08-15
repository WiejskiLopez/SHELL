"""SQL ORM model <-> domain entity mappers for Project aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)
from shell.project_service.domain.project.aggregates.project.project import Project
from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
    ProjectId,
)
from shell.project_service.domain.project.aggregates.project.value_objects.project_name import (
    ProjectName,
)
from shell.project_service.domain.project.aggregates.project.value_objects.project_status import (
    ProjectStatus,
)
from shell.project_service.domain.project.aggregates.project.value_objects.repo_url import RepoUrl

if TYPE_CHECKING:
    from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
        ProjectModel,
    )


def project_model_to_entity(model: ProjectModel) -> Project:
    return Project.restore(
        id=ProjectId(model.id),
        name=ProjectName(model.name),
        repo_url=RepoUrl(model.repo_url),
        status=ProjectStatus(model.status),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at)),
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at)),
    )
