from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.session.aggregates.session_state.value_objects.session_state_id import (
        SessionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class SessionStateUpdatedEvent(DomainEvent):
    sessionstate_id: SessionStateId

    @classmethod
    def now(cls, sessionstate_id: SessionStateId, now: CreatedAt) -> SessionStateUpdatedEvent:
        return cls(occurred_at=now, sessionstate_id=sessionstate_id)
