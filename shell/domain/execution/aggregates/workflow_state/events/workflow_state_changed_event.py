from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.aggregates.workflow_state.value_objects.workflow_state_id import (
    WorkflowStateId,
)
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion
from shell.domain.platform.value_objects.state_direction import StateDirection


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
        now: CreatedAt,
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
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            workflow_id=WorkflowId(payload["workflow_id"]),
            workflow_state_id=WorkflowStateId(payload["workflow_state_id"]),
            direction=StateDirection(payload["direction"]),
            key=payload["key"],
            old_value=payload["old_value"],
            new_value=payload["new_value"],
        )
