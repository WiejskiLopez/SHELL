from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class TaskExecutionDeletedEvent(DomainEvent):
    task_execution_id: TaskExecutionId

    @classmethod
    def now(cls, task_execution_id: TaskExecutionId, now: OccurredAt) -> TaskExecutionDeletedEvent:
        return cls(occurred_at=now, task_execution_id=task_execution_id)
