from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )
    from shell.platform.domain.value_objects.created_at import CreatedAt

@dataclass(frozen=True, slots=True)
class WorkflowStateChangedEvent(DomainEvent):
    workflow_id: WorkflowId
    workflow_state_id: WorkflowStateId

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        workflow_state_id: WorkflowStateId,
        now: CreatedAt,
    ) -> WorkflowStateChangedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            workflow_state_id=workflow_state_id,
        )
