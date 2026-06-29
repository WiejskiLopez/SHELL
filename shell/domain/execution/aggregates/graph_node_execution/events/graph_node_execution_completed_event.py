from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.aggregates.workflow.value_objects.graph_node_execution_result_id import (
    GraphNodeExecutionResultId,
)
from shell.domain.execution.aggregates.workflow.value_objects.workflow_id import WorkflowId
from shell.domain.execution.value_objects.node_role import NodeRole
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionCompletedEvent(DomainEvent):
    node_id: GraphNodeExecutionId
    role: NodeRole
    result: StateData | None = None
    workflow_id: WorkflowId | None = None
    result_id: GraphNodeExecutionResultId | None = None

    @property
    def graph_node_execution_id(self) -> GraphNodeExecutionId:
        return self.node_id

    @classmethod
    def now(
        cls,
        node_id: GraphNodeExecutionId,
        now: CreatedAt,
        role: NodeRole | None = None,
        result: StateData | None = None,
        workflow_id: WorkflowId | None = None,
        result_id: GraphNodeExecutionResultId | None = None,
    ) -> GraphNodeExecutionCompletedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            role=role or NodeRole.AGENT,
            result=result,
            workflow_id=workflow_id,
            result_id=result_id,
        )
