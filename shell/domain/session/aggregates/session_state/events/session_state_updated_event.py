from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.session.aggregates.session_state.value_objects.session_state_id import (
        SessionStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class SessionStateUpdatedEvent(DomainEvent):
    session_state_id: SessionStateId

    @classmethod
    def now(cls, session_state_id: SessionStateId, now: OccurredAt) -> SessionStateUpdatedEvent:
        return cls(occurred_at=now, session_state_id=session_state_id)
