from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId
    from shell.session.domain.session.aggregates.session_state.value_objects.session_state_id import (
        SessionStateId,
    )


@dataclass(frozen=True, slots=True)
class SessionStateChangedEvent(DomainEvent):
    session_id: SessionId
    session_state_id: SessionStateId

    @classmethod
    def now(
        cls,
        session_id: SessionId,
        session_state_id: SessionStateId,
        now: OccurredAt,
    ) -> SessionStateChangedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
            session_state_id=session_state_id,
        )
