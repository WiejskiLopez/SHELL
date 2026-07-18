from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import TaskExecutionStateId
    from shell.platform.domain.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class TaskExecutionStateCreatedEvent(DomainEvent):
    taskexecutionstate_id: TaskExecutionStateId

    @classmethod
    def now(cls, taskexecutionstate_id: TaskExecutionStateId, now: CreatedAt) -> "TaskExecutionStateCreatedEvent":
        return cls(occurred_at=now, taskexecutionstate_id=taskexecutionstate_id)
