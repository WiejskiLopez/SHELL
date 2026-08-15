from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class SessionExecutionDeletedEvent(DomainEvent):
    session_execution_id: SessionExecutionId

    @classmethod
    def now(
        cls, session_execution_id: SessionExecutionId, now: OccurredAt
    ) -> SessionExecutionDeletedEvent:
        return cls(occurred_at=now, session_execution_id=session_execution_id)
