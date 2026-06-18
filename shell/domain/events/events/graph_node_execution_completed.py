from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.events.events import DomainEvent
from shell.domain.value_objects.ids import (
    GraphNodeExecutionId,
    GraphNodeExecutionResultId,
    WorkflowId,
)


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionCompleted(DomainEvent):
    graph_node_execution_id: GraphNodeExecutionId
    workflow_id: WorkflowId
    graph_node_execution_result_id: GraphNodeExecutionResultId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
            graph_node_execution_result_id=GraphNodeExecutionResultId(
                payload["graph_node_execution_result_id"]
            ),
        )

    @classmethod
    def now(
        cls,
        graph_node_execution_id: GraphNodeExecutionId,
        workflow_id: WorkflowId,
        graph_node_execution_result_id: GraphNodeExecutionResultId,
        now: datetime,
    ) -> GraphNodeExecutionCompleted:
        return cls(
            occurred_at=now,
            graph_node_execution_id=graph_node_execution_id,
            workflow_id=workflow_id,
            graph_node_execution_result_id=graph_node_execution_result_id,
        )
