from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution_state.value_objects.session_execution_state_id import (
        SessionExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class SessionExecutionStateCreatedEvent(DomainEvent):
    sessionexecutionstate_id: SessionExecutionStateId

    @classmethod
    def now(cls, sessionexecutionstate_id: SessionExecutionStateId, now: CreatedAt) -> SessionExecutionStateCreatedEvent:
        return cls(occurred_at=now, sessionexecutionstate_id=sessionexecutionstate_id)
