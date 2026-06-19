from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId, WorkflowId


@dataclass(frozen=True, slots=True)
class GraphNodeParallelExecutionRequestedEvent(DomainEvent):
    workflow_id: WorkflowId
    fork_node_execution_id: GraphNodeExecutionId
    parallel_target_node_ids: tuple[GraphNodeExecutionId, ...]
    parallel_group_id: str

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        fork_node_execution_id: GraphNodeExecutionId,
        parallel_target_node_ids: tuple[GraphNodeExecutionId, ...],
        parallel_group_id: str,
        now: datetime,
    ) -> GraphNodeParallelExecutionRequestedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            fork_node_execution_id=fork_node_execution_id,
            parallel_target_node_ids=parallel_target_node_ids,
            parallel_group_id=parallel_group_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            fork_node_execution_id=GraphNodeExecutionId(payload["fork_node_execution_id"]),
            parallel_target_node_ids=tuple(
                GraphNodeExecutionId(nid) for nid in payload["parallel_target_node_ids"]
            ),
            parallel_group_id=payload["parallel_group_id"],
        )
