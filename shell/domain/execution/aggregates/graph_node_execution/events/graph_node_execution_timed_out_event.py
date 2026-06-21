from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId
from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionTimedOutEvent(DomainEvent):
    workflow_id: WorkflowId
    graph_node_execution_id: GraphNodeExecutionId
    timeout_seconds: int

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        graph_node_execution_id: GraphNodeExecutionId,
        timeout_seconds: int,
        now: datetime,
    ) -> GraphNodeExecutionTimedOutEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            graph_node_execution_id=graph_node_execution_id,
            timeout_seconds=timeout_seconds,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
            timeout_seconds=payload["timeout_seconds"],
        )
