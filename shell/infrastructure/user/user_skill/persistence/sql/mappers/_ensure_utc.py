"""SQL ORM model <-> domain entity mappers for UserSkill aggregate."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.user.aggregates.user_skill.user_skill import UserSkill
from shell.domain.user.value_objects.skill_data import SkillData
from shell.domain.user.value_objects.skill_id import SkillId
from shell.domain.user.value_objects.user_id import UserId
from shell.infrastructure.user.user_skill.persistence.sql.models.user_skill import UserSkillModel
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

