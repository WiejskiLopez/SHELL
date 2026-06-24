from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.workflow.value_objects.graph_node_execution_result_id import (
    GraphNodeExecutionResultId,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class WorkflowGraphNodeExecutionCompletedEvent(DomainEvent):
    graph_node_execution_id: GraphNodeExecutionId
    workflow_id: WorkflowId
    result_id: GraphNodeExecutionResultId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
            workflow_id=WorkflowId(payload["workflow_id"]),
            result_id=GraphNodeExecutionResultId(payload["result_id"]),
        )

    @classmethod
    def now(
        cls,
        graph_node_execution_id: GraphNodeExecutionId,
        workflow_id: WorkflowId,
        result_id: GraphNodeExecutionResultId,
        now: datetime,
    ) -> WorkflowGraphNodeExecutionCompletedEvent:
        return cls(
            occurred_at=now,
            graph_node_execution_id=graph_node_execution_id,
            workflow_id=workflow_id,
            result_id=result_id,
        )
