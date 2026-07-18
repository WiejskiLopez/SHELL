from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class TaskExecutionUpdatedEvent(DomainEvent):
    taskexecution_id: TaskExecutionId

    @classmethod
    def now(cls, taskexecution_id: TaskExecutionId, now: CreatedAt) -> TaskExecutionUpdatedEvent:
        return cls(occurred_at=now, taskexecution_id=taskexecution_id)
