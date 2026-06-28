from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.user.value_objects.skill_id import SkillId
from shell.domain.user.value_objects.skill_payload import SkillPayload
from shell.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class UserSkill:
    id: SkillId
    user_id: UserId
    payload: SkillPayload
    created_at: CreatedAt

    @classmethod
    def new(cls, user_id: UserId, payload: dict, now: CreatedAt | None = None) -> UserSkill:
        return cls(
            id=SkillId.generate(),
            user_id=user_id,
            payload=SkillPayload(payload),
            created_at=now or CreatedAt.now(),
        )
