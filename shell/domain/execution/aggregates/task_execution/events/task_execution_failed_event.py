from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.reason import Reason


@dataclass(frozen=True, slots=True)
class TaskExecutionFailedEvent(DomainEvent):
    task_execution_id: TaskExecutionId
    reason: Reason

    @classmethod
    def now(
        cls,
        task_execution_id: TaskExecutionId,
        reason: Reason,
        now: CreatedAt,
    ) -> TaskExecutionFailedEvent:
        return cls(
            occurred_at=now,
            task_execution_id=task_execution_id,
            reason=reason,
        )
