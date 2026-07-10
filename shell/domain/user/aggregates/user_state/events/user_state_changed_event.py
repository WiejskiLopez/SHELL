from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
    from shell.domain.user.value_objects.user_id import UserId
    from shell.platform.domain.value_objects.created_at import CreatedAt
    from shell.platform.domain.value_objects.state_direction import StateDirection


@dataclass(frozen=True, slots=True, kw_only=True)
class UserStateChangedEvent(DomainEvent):
    user_id: UserId
    user_state_id: UserStateId
    direction: StateDirection
    key: str
    old_value: object | None
    new_value: object | None

    @classmethod
    def now(
        cls,
        *,
        user_id: UserId,
        user_state_id: UserStateId,
        direction: StateDirection,
        key: str,
        old_value: object | None,
        new_value: object | None,
        now: CreatedAt,
    ) -> UserStateChangedEvent:
        return cls(
            occurred_at=now,
            user_id=user_id,
            user_state_id=user_state_id,
            direction=direction,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )
