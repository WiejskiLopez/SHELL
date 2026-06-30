from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class WorkflowCompletedEvent(DomainEvent):
    workflow_id: WorkflowId
    task_execution_id: TaskExecutionId | None = None

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        task_id = payload["task_execution_id"]
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            workflow_id=WorkflowId(payload["workflow_id"]),
            task_execution_id=TaskExecutionId(task_id) if task_id else None,
        )

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        now: CreatedAt,
        task_execution_id: TaskExecutionId | None = None,
    ) -> WorkflowCompletedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_execution_id=task_execution_id,
        )
