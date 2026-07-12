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


def user_skill_model_to_entity(model: UserSkillModel) -> UserSkill:
    return UserSkill.restore(
        id=SkillId(model.id),
        user_id=UserId(model.user_id),
        skill_data=SkillData(JsonStr(json.dumps(dict(model.skill_data)))) if model.skill_data else SkillData(JsonStr(json.dumps({}))),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_skill_entity_to_model(entity: UserSkill) -> UserSkillModel:
    return UserSkillModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        skill_data=json.dumps(json.loads(entity.skill_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
    )
