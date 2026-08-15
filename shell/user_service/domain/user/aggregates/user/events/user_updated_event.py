from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.user_service.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True)
class UserUpdatedEvent(DomainEvent):
    user_id: UserId

    @classmethod
    def now(cls, user_id: UserId, now: OccurredAt) -> UserUpdatedEvent:
        return cls(occurred_at=now, user_id=user_id)
