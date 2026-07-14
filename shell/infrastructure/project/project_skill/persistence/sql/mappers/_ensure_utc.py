"""SQL ORM model <-> domain entity mappers for ProjectSkill aggregate."""

from __future__ import annotations

import json
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
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

