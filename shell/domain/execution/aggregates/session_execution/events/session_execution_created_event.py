from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


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
