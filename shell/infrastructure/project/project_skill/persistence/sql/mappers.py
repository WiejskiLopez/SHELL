"""SQL ORM model <-> domain entity mappers for ProjectSkill aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project_skill.project_skill import ProjectSkill
from shell.domain.project.aggregates.project_skill.value_objects.project_skill_data import (
    ProjectSkillData,
)
from shell.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
    ProjectSkillId,
)
from shell.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
    ProjectSkillModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


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
