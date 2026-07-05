from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.user.value_objects.skill_id import SkillId
    from shell.domain.user.value_objects.user_id import UserId

@dataclass(frozen=True, slots=True, kw_only=True)
class UserSkillCreatedEvent(DomainEvent):
    skill_id: SkillId
    user_id: UserId

    @classmethod
    def now(
        cls,
        *,
        skill_id: SkillId,
        user_id: UserId,
        now: CreatedAt,
    ) -> UserSkillCreatedEvent:
        return cls(
            occurred_at=now,
            skill_id=skill_id,
            user_id=user_id,
        )
