from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.platform.events import DomainEvent
from shell.domain.execution.value_objects.ids import (
    GraphNodeExecutionId,
    WorkflowId,
)


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionWaitingEvent(DomainEvent):
    workflow_id: WorkflowId
    graph_node_execution_id: GraphNodeExecutionId
    child_graph_ids: tuple[str, ...] = ()

    @classmethod
    def now(
        cls,
        workflow_id: WorkflowId,
        graph_node_execution_id: GraphNodeExecutionId,
        child_graph_ids: tuple[str, ...] = (),
        now: datetime | None = None,
    ) -> GraphNodeExecutionWaitingEvent:
        from datetime import datetime as dt

        return cls(
            occurred_at=now or dt.now(),
            workflow_id=workflow_id,
            graph_node_execution_id=graph_node_execution_id,
            child_graph_ids=child_graph_ids,
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
            child_graph_ids=tuple(payload.get("child_graph_ids", [])),
        )
