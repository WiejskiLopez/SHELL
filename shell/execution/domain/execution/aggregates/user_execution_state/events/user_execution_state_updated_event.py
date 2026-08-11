from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id import (
        UserExecutionStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class UserExecutionStateUpdatedEvent(DomainEvent):
    user_execution_state_id: UserExecutionStateId

    @classmethod
    def now(
        cls, user_execution_state_id: UserExecutionStateId, now: OccurredAt
    ) -> UserExecutionStateUpdatedEvent:
        return cls(occurred_at=now, user_execution_state_id=user_execution_state_id)
