from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    GraphNodeTransitionExecutionId,
    WorkflowId
)


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionJoinReadyEvent(DomainEvent):
    workflow_id: WorkflowId
    join_node_execution_id: GraphNodeExecutionId
    join_transition_id: GraphNodeTransitionExecutionId
    completed_source_ids: tuple[GraphNodeExecutionId, ...]

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        join_node_execution_id: GraphNodeExecutionId,
        join_transition_id: GraphNodeTransitionExecutionId,
        completed_source_ids: tuple[GraphNodeExecutionId, ...],
        now: datetime,
    ) -> GraphNodeExecutionJoinReadyEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            join_node_execution_id=join_node_execution_id,
            join_transition_id=join_transition_id,
            completed_source_ids=completed_source_ids,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            join_node_execution_id=GraphNodeExecutionId(payload["join_node_execution_id"]),
            join_transition_id=GraphNodeTransitionExecutionId(payload["join_transition_id"]),
            completed_source_ids=tuple(
                GraphNodeExecutionId(nid) for nid in payload["completed_source_ids"]
            ),
        )
