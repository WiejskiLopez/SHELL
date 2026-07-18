from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user_state.value_objects.user_state_id import UserStateId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class UserStateDeletedEvent(DomainEvent):
    userstate_id: UserStateId

    @classmethod
    def now(cls, userstate_id: UserStateId, now: CreatedAt) -> UserStateDeletedEvent:
        return cls(occurred_at=now, userstate_id=userstate_id)
