from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.value_objects.state_kind import StateKind
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class SessionStateChangedEvent(DomainEvent):
    session_id: str
    session_state_id: str
    kind: str
    key: str
    old_value: object | None = None
    new_value: object | None = None

    @classmethod
    def now(
        cls,
        session_id: str,
        session_state_id: str,
        kind: StateKind,
        key: str,
        now: datetime,
        old_value: object | None = None,
        new_value: object | None = None,
    ) -> SessionStateChangedEvent:
        return cls(
            occurred_at=now,
            session_id=session_id,
            session_state_id=session_state_id,
            kind=kind.value,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )
