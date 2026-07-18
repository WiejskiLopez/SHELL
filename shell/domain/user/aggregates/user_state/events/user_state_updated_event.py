from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user_state.value_objects.UserStateId import UserStateId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class UserStateUpdatedEvent(DomainEvent):
    userstate_id: UserStateId

    @classmethod
    def now(cls, userstate_id: UserStateId, now: CreatedAt) -> "UserStateUpdatedEvent":
        return cls(occurred_at=now, userstate_id=userstate_id)
