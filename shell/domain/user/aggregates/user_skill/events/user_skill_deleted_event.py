from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class UserSkillDeletedEvent(DomainEvent):
    userskill_id: UserSkillId

    @classmethod
    def now(cls, userskill_id: UserSkillId, now: CreatedAt) -> UserSkillDeletedEvent:
        return cls(occurred_at=now, userskill_id=userskill_id)
