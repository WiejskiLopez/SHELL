from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.user.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId


@dataclass(frozen=True, slots=True)
class UserStateDeletedEvent(DomainEvent):
    user_state_id: UserStateId

    @classmethod
    def now(cls, user_state_id: UserStateId, now: OccurredAt) -> UserStateDeletedEvent:
        return cls(occurred_at=now, user_state_id=user_state_id)
