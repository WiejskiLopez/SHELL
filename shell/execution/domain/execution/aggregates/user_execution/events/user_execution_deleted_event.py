from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class UserExecutionDeletedEvent(DomainEvent):
    user_execution_id: UserExecutionId

    @classmethod
    def now(cls, user_execution_id: UserExecutionId, now: OccurredAt) -> UserExecutionDeletedEvent:
        return cls(occurred_at=now, user_execution_id=user_execution_id)
