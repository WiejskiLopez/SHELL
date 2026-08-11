from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.user.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
    from shell.user.domain.user.value_objects.user_id import UserId


@dataclass(frozen=True, slots=True, kw_only=True)
class UserStateChangedEvent(DomainEvent):
    user_id: UserId
    user_state_id: UserStateId

    @classmethod
    def now(
        cls,
        *,
        user_id: UserId,
        user_state_id: UserStateId,
        now: OccurredAt,
    ) -> UserStateChangedEvent:
        return cls(
            occurred_at=now,
            user_id=user_id,
            user_state_id=user_state_id,
        )
