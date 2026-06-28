from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class WorkflowPausedEvent(DomainEvent):
    workflow_id: WorkflowId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
        )

    @classmethod
    def now(
        cls, workflow_id: WorkflowId, now: datetime
    ) -> WorkflowPausedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
        )
