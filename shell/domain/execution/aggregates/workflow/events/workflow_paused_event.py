from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class WorkflowPausedEvent(DomainEvent):
    workflow_id: WorkflowId

    @classmethod
    def now(cls, workflow_id: WorkflowId, now: CreatedAt) -> WorkflowPausedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
        )
