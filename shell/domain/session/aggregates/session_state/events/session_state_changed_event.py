from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.session.aggregates.session.value_objects.session_id import SessionId
from shell.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class SessionStateChangedEvent(DomainEvent):
    session_id: SessionId
    session_state_id: SessionStateId
    direction: str
    key: str
    old_value: object | None = None
    new_value: object | None = None

    @classmethod
    def now(
        cls,
        session_id: SessionId,
        session_state_id: SessionStateId,
        direction: StateDirection,
        key: str,
        now: datetime,
        old_value: object | None = None,
        new_value: object | None = None,
    ) -> SessionStateChangedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
            session_state_id=session_state_id,
            direction=direction.value,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            session_id=SessionId(payload.get("session_id")),
            session_state_id=SessionStateId(payload.get("session_state_id")),
            direction=payload.get("direction"),
            key=payload.get("key"),
            old_value=payload.get("old_value"),
            new_value=payload.get("new_value"),
        )
