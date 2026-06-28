from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId


@dataclass(frozen=True, slots=True)
class SessionClosedEvent(DomainEvent):
    session_id: SessionId

    @classmethod
    def now(
        cls,
        session_id: SessionId,
        now: datetime,
    ) -> SessionClosedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            session_id=SessionId(payload["session_id"]),
        )
