"""SQL ORM model <-> domain entity mappers for UserSkill aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.user_service.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
    UserSkillModel,
)

if TYPE_CHECKING:
    from shell.user_service.domain.user.aggregates.user_skill.user_skill import UserSkill


def user_skill_entity_to_model(entity: UserSkill) -> UserSkillModel:
    return UserSkillModel(
        id=entity.id.value,
        user_id=entity.user_id.value,
        skill_data=json.dumps(json.loads(entity.skill_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
    )
