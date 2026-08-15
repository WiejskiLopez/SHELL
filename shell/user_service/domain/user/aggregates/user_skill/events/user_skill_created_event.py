from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.user_service.domain.user.aggregates.user_skill.value_objects.user_skill_id import (
        UserSkillId,
    )
    from shell.user_service.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class UserSkillCreatedEvent(DomainEvent):
    skill_id: UserSkillId
    user_id: UserId

    @classmethod
    def now(
        cls,
        *,
        skill_id: UserSkillId,
        user_id: UserId,
        now: OccurredAt,
    ) -> UserSkillCreatedEvent:
        return cls(
            occurred_at=now,
            skill_id=skill_id,
            user_id=user_id,
        )
