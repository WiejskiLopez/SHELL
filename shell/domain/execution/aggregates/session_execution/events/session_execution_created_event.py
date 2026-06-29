from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class SessionExecutionCreatedEvent(DomainEvent):
    session_execution_id: SessionExecutionId

    @classmethod
    def now(
        cls,
        session_execution_id: SessionExecutionId,
        now: CreatedAt,
    ) -> SessionExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            session_execution_id=session_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            session_execution_id=SessionExecutionId(payload["session_execution_id"]),
        )
