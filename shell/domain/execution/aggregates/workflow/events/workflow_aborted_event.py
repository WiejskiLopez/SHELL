from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
        TaskExecutionId,
    )
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.platform.value_objects.created_at import CreatedAt
    from shell.domain.platform.value_objects.reason import Reason


@dataclass(frozen=True, slots=True)
class WorkflowAbortedEvent(DomainEvent):
    workflow_id: WorkflowId
    reason: Reason | None = None
    task_execution_id: TaskExecutionId | None = None

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        now: CreatedAt,
        reason: Reason | None = None,
        task_execution_id: TaskExecutionId | None = None,
    ) -> WorkflowAbortedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            reason=reason,
            task_execution_id=task_execution_id,
        )
