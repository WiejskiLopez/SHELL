from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id import (
        UserExecutionStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class UserExecutionStateDeletedEvent(DomainEvent):
    user_execution_state_id: UserExecutionStateId

    @classmethod
    def now(
        cls, user_execution_state_id: UserExecutionStateId, now: CreatedAt
    ) -> UserExecutionStateDeletedEvent:
        return cls(occurred_at=now, user_execution_state_id=user_execution_state_id)
