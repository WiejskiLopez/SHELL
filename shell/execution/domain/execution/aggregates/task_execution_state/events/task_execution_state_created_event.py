from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
        TaskExecutionStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class TaskExecutionStateCreatedEvent(DomainEvent):
    task_execution_state_id: TaskExecutionStateId

    @classmethod
    def now(
        cls, task_execution_state_id: TaskExecutionStateId, now: OccurredAt
    ) -> TaskExecutionStateCreatedEvent:
        return cls(occurred_at=now, task_execution_state_id=task_execution_state_id)
