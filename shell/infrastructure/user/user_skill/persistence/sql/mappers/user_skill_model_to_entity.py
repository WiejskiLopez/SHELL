"""SQL ORM model <-> domain entity mappers for UserSkill aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user_skill.user_skill import UserSkill
from shell.domain.user.value_objects.skill_data import SkillData
from shell.domain.user.value_objects.skill_id import SkillId
from shell.domain.user.value_objects.user_id import UserId
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

from ._ensure_utc import _ensure_utc

if TYPE_CHECKING:
    from shell.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
        UserSkillModel,
    )


def user_skill_model_to_entity(model: UserSkillModel) -> UserSkill:
    return UserSkill.restore(
        id=SkillId(model.id),
        user_id=UserId(model.user_id),
        skill_data=SkillData(JsonStr(json.dumps(dict(model.skill_data)))) if model.skill_data else SkillData(JsonStr(json.dumps({}))),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )

