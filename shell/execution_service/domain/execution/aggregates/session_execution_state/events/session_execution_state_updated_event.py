from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.session_execution_state.value_objects.session_execution_state_id import (
        SessionExecutionStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class SessionExecutionStateUpdatedEvent(DomainEvent):
    session_execution_state_id: SessionExecutionStateId

    @classmethod
    def now(
        cls, session_execution_state_id: SessionExecutionStateId, now: OccurredAt
    ) -> SessionExecutionStateUpdatedEvent:
        return cls(occurred_at=now, session_execution_state_id=session_execution_state_id)
