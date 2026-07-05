from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.session.aggregates.session.value_objects.session_id import SessionId


@dataclass(frozen=True, slots=True)
class SessionClosedEvent(DomainEvent):
    session_id: SessionId

    @classmethod
    def now(
        cls,
        session_id: SessionId,
        now: CreatedAt,
    ) -> SessionClosedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
        )
