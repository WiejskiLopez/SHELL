"""SQL ORM model <-> domain entity mappers for ProjectSkill aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.project.aggregates.project.value_objects.project_id import ProjectId
from shell.domain.project.aggregates.project_skill.project_skill import ProjectSkill
from shell.domain.project.aggregates.project_skill.value_objects.project_skill_data import (
    ProjectSkillData,
)
from shell.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
    ProjectSkillId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
        ProjectSkillModel,
    )


def project_skill_model_to_entity(model: ProjectSkillModel) -> ProjectSkill:
    return ProjectSkill.restore(
        id=ProjectSkillId(model.id),
        project_id=ProjectId(model.project_id),
        skill_data=ProjectSkillData(JsonStr(json.dumps(dict(model.skill_data))))
        if model.skill_data
        else ProjectSkillData(JsonStr(json.dumps({}))),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at))
        if model.updated_at is not None
        else None,
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at))
        if model.deleted_at is not None
        else None,
    )
