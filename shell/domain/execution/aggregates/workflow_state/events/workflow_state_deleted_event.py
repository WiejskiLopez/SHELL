from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.platform.domain.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
        WorkflowStateId,
    )
    from shell.platform.domain.value_objects.occurred_at import OccurredAt


@dataclass(frozen=True, slots=True)
class WorkflowStateDeletedEvent(DomainEvent):
    workflow_state_id: WorkflowStateId

    @classmethod
    def now(cls, workflow_state_id: WorkflowStateId, now: OccurredAt) -> WorkflowStateDeletedEvent:
        return cls(occurred_at=now, workflow_state_id=workflow_state_id)
