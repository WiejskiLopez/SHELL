from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.occurred_at import OccurredAt
    from shell.session.domain.session.aggregates.session.value_objects.session_id import SessionId


@dataclass(frozen=True, slots=True)
class SessionClosedEvent(DomainEvent):
    session_id: SessionId

    @classmethod
    def now(
        cls,
        session_id: SessionId,
        now: OccurredAt,
    ) -> SessionClosedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
        )
