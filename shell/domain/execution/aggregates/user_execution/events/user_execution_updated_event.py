from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.value_objects.UserExecutionId import UserExecutionId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class UserExecutionUpdatedEvent(DomainEvent):
    userexecution_id: UserExecutionId

    @classmethod
    def now(cls, userexecution_id: UserExecutionId, now: CreatedAt) -> "UserExecutionUpdatedEvent":
        return cls(occurred_at=now, userexecution_id=userexecution_id)
