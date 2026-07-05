from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class UserDeletedEvent(DomainEvent):
    user_id: UserId

    @classmethod
    def now(cls, user_id: UserId, now: CreatedAt) -> UserDeletedEvent:
        return cls(occurred_at=now, user_id=user_id)
