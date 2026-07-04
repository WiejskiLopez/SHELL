from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId

from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.value_objects.error_description import ErrorDescription
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class NodeExecutionFailedEvent(DomainEvent):
    node_id: NodeExecutionId
    role: NodeRole
    error: ErrorDescription
    workflow_id: WorkflowId | None = None

    @property
    def node_execution_id(self) -> NodeExecutionId:
        return self.node_id

    @property
    def reason(self) -> str:
        return self.error.value

    @classmethod
    def now(
        cls,
        node_id: NodeExecutionId,
        now: CreatedAt,
        role: NodeRole | None = None,
        error: ErrorDescription | None = None,
        workflow_id: WorkflowId | None = None,
        reason: str | None = None,
    ) -> NodeExecutionFailedEvent:
        actual_error = (
            error
            if error is not None
            else (ErrorDescription(reason) if reason else ErrorDescription("unknown error"))
        )
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role or NodeRole.AGENT,
            error=actual_error,
            workflow_id=workflow_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            node_id=NodeExecutionId(payload["node_id"]),
            role=NodeRole(payload["role"]),
            error=ErrorDescription(payload.get("error") or "unknown error"),
        )
