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


@dataclass(frozen=True, slots=True)
class WorkflowStartedEvent(DomainEvent):
    workflow_id: WorkflowId
    task_execution_id: TaskExecutionId | None = None
    work_dir: str | None = None

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        now: CreatedAt,
        task_execution_id: TaskExecutionId | None = None,
        work_dir: str | None = None,
    ) -> WorkflowStartedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            task_execution_id=task_execution_id,
            work_dir=work_dir,
        )
