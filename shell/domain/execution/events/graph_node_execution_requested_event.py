from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.ids import GraphNodeExecutionId, WorkflowId


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionRequestedEvent(DomainEvent):
    """Request to execute exactly one node identified by ``node_execution_id``.

    Emitted by the Workflow aggregate (start_at / advance_to) and dispatched
    via the EventBus to ``GraphNodeExecutionWorker``. The worker is expected to be
    idempotent: it must compare the request against ``Workflow.cursor`` and
    no-op if they do not match (re-delivery / out-of-order delivery).
    """

    workflow_id: WorkflowId
    graph_node_execution_id: GraphNodeExecutionId

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            workflow_id=WorkflowId(payload["workflow_id"]),
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
        )

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> GraphNodeExecutionRequestedEvent:
        return cls(
            occurred_at=now,
            workflow_id=workflow_id,
            graph_node_execution_id=graph_node_execution_id,
        )
