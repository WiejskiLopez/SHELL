from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.task_execution_id import TaskExecutionId
from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class WorkflowAbortedEvent(DomainEvent):
    workflow_id: WorkflowId
    task_execution_id: TaskExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_execution_id=TaskExecutionId(payload["task_execution_id"]),
        )

    @classmethod
    def now(
        cls, workflow_id: WorkflowId, task_execution_id: TaskExecutionId, now: datetime
    ) -> WorkflowAbortedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_execution_id=task_execution_id,
        )
