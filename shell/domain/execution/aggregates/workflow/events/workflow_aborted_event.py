from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import TaskExecutionId
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class WorkflowAbortedEvent(DomainEvent):
    workflow_id: WorkflowId
    task_execution_id: TaskExecutionId | None = None

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        task_id = payload.get("task_execution_id")
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload.get("workflow_id")),
            task_execution_id=TaskExecutionId(task_id) if task_id else None,
        )

    @classmethod
    def now(
        cls, workflow_id: WorkflowId, now: datetime, task_execution_id: TaskExecutionId | None = None
    ) -> WorkflowAbortedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_execution_id=task_execution_id,
        )
