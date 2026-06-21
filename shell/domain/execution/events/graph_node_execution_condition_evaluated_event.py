from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    GraphNodeTransitionExecutionId,
    WorkflowId,
)
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionConditionEvaluatedEvent(DomainEvent):
    workflow_id: WorkflowId
    source_node_execution_id: GraphNodeExecutionId
    transition_id: GraphNodeTransitionExecutionId
    condition_expression: str
    condition_result: bool
    target_node_execution_id: GraphNodeExecutionId | None

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        source_node_execution_id: GraphNodeExecutionId,
        transition_id: GraphNodeTransitionExecutionId,
        condition_expression: str,
        condition_result: bool,
        target_node_execution_id: GraphNodeExecutionId | None,
        now: datetime,
    ) -> GraphNodeExecutionConditionEvaluatedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            source_node_execution_id=source_node_execution_id,
            transition_id=transition_id,
            condition_expression=condition_expression,
            condition_result=condition_result,
            target_node_execution_id=target_node_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            source_node_execution_id=GraphNodeExecutionId(payload["source_node_execution_id"]),
            transition_id=GraphNodeTransitionExecutionId(payload["transition_id"]),
            condition_expression=payload["condition_expression"],
            condition_result=payload["condition_result"],
            target_node_execution_id=(
                GraphNodeExecutionId(payload["target_node_execution_id"])
                if payload.get("target_node_execution_id")
                else None
            ),
        )
