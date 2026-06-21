from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.ids.graph_node_transition_execution_id import (
    GraphNodeTransitionExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import GraphNodeExecutionId
from shell.domain.execution.aggregates.workflow.workflow_id import WorkflowId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionLoopIterationEvent(DomainEvent):
    workflow_id: WorkflowId
    loop_node_execution_id: GraphNodeExecutionId
    loop_transition_id: GraphNodeTransitionExecutionId
    current_iteration: int
    max_loop_count: int
    should_continue: bool

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        loop_node_execution_id: GraphNodeExecutionId,
        loop_transition_id: GraphNodeTransitionExecutionId,
        current_iteration: int,
        max_loop_count: int,
        should_continue: bool,
        now: datetime,
    ) -> GraphNodeExecutionLoopIterationEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            loop_node_execution_id=loop_node_execution_id,
            loop_transition_id=loop_transition_id,
            current_iteration=current_iteration,
            max_loop_count=max_loop_count,
            should_continue=should_continue,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            loop_node_execution_id=GraphNodeExecutionId(payload["loop_node_execution_id"]),
            loop_transition_id=GraphNodeTransitionExecutionId(payload["loop_transition_id"]),
            current_iteration=payload["current_iteration"],
            max_loop_count=payload["max_loop_count"],
            should_continue=payload["should_continue"],
        )
