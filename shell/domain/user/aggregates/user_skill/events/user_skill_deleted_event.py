from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user_skill.value_objects.SkillId import SkillId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class UserSkillDeletedEvent(DomainEvent):
    userskill_id: SkillId

    @classmethod
    def now(cls, userskill_id: SkillId, now: CreatedAt) -> "UserSkillDeletedEvent":
        return cls(occurred_at=now, userskill_id=userskill_id)
