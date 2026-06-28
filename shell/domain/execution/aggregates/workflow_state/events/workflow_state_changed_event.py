from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.execution.value_objects.state_direction import StateDirection
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class WorkflowStateChangedEvent(DomainEvent):
    workflow_id: WorkflowId
    workflow_state_id: WorkflowStateId
    direction: StateDirection
    key: str
    old_value: object | None = None
    new_value: object | None = None

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        workflow_state_id: WorkflowStateId,
        direction: StateDirection,
        key: str,
        now: datetime,
        old_value: object | None = None,
        new_value: object | None = None,
    ) -> WorkflowStateChangedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            workflow_state_id=workflow_state_id,
            direction=direction,
            key=key,
            old_value=old_value,
            new_value=new_value,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload.get("workflow_id")),
            workflow_state_id=WorkflowStateId(payload.get("workflow_state_id")),
            direction=StateDirection(payload.get("direction")),
            key=payload.get("key"),
            old_value=payload.get("old_value"),
            new_value=payload.get("new_value"),
        )
