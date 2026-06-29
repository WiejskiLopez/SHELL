from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


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

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            session_id=SessionId(payload["session_id"]),
        )
