"""SQL ORM model <-> domain entity mappers for Project BC."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.deleted_at import DeletedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.domain.platform.value_objects.updated_at import UpdatedAt
from shell.domain.project.aggregates.project.project import Project
from shell.domain.project.aggregates.project_skill.project_skill import ProjectSkill
from shell.domain.project.aggregates.project_state.project_state import ProjectState
from shell.domain.project.aggregates.project_state.value_objects.project_state_id import (
    ProjectStateId,
)
from shell.domain.project.value_objects.project_id import ProjectId
from shell.domain.project.value_objects.project_name import ProjectName
from shell.domain.project.value_objects.project_skill_data import ProjectSkillData
from shell.domain.project.value_objects.project_skill_id import ProjectSkillId
from shell.domain.project.value_objects.project_status import ProjectStatus
from shell.domain.project.value_objects.repo_url import RepoUrl
from shell.infrastructure.project.persistence.sql.models.project import ProjectModel
from shell.infrastructure.project.persistence.sql.models.project_skill import (
    ProjectSkillModel,
)
from shell.infrastructure.project.persistence.sql.models.project_state import (
    ProjectStateModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


# ── Project ────────────────────────────────────────────────────────────────────────


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


# ── ProjectSkill ────────────────────────────────────────────────────────────────────


def project_skill_model_to_entity(model: ProjectSkillModel) -> ProjectSkill:
    return ProjectSkill.restore(
        id=ProjectSkillId(model.id),
        project_id=ProjectId(model.project_id),
        skill_data=ProjectSkillData(dict(model.skill_data))
        if model.skill_data
        else ProjectSkillData({}),
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


def project_skill_entity_to_model(entity: ProjectSkill) -> ProjectSkillModel:
    return ProjectSkillModel(
        id=entity.id.value,
        project_id=entity.project_id.value,
        skill_data=entity.skill_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value if entity.updated_at else None,
        deleted_at=entity.deleted_at.value if entity.deleted_at else None,
    )


# ── ProjectState ────────────────────────────────────────────────────────────────────


def project_state_model_to_entity(model: ProjectStateModel) -> ProjectState:
    return ProjectState.restore(
        id=ProjectStateId(model.id),
        project_id=ProjectId(model.project_id),
        direction=StateDirection(model.direction),
        is_current=bool(model.is_current),
        state_data=StateData(dict(model.state_data))
        if model.state_data
        else StateData({}),
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


def project_state_entity_to_model(entity: ProjectState) -> ProjectStateModel:
    return ProjectStateModel(
        id=entity.id.value,
        project_id=entity.project_id.value,
        direction=entity.direction.value,
        state_data=entity.snapshot(),
        is_current=entity.is_current,
        created_at=entity.created_at.value if entity.created_at else None,
        updated_at=entity.updated_at.value if entity.updated_at else None,
        deleted_at=entity.deleted_at.value if entity.deleted_at else None,
    )
