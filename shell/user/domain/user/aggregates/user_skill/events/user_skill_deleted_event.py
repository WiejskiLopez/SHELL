from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.user.domain.user.aggregates.user_skill.value_objects.user_skill_id import UserSkillId


@dataclass(frozen=True, slots=True)
class UserSkillDeletedEvent(DomainEvent):
    user_skill_id: UserSkillId

    @classmethod
    def now(cls, user_skill_id: UserSkillId, now: OccurredAt) -> UserSkillDeletedEvent:
        return cls(occurred_at=now, user_skill_id=user_skill_id)
