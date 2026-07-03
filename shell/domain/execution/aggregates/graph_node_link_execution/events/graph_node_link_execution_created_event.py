from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
        GraphExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
        GraphNodeExecutionId,
    )
    from shell.domain.execution.aggregates.graph_node_link_execution.value_objects.graph_node_link_execution_id import (
        GraphNodeLinkExecutionId,
    )


@dataclass(frozen=True, slots=True)
class GraphNodeLinkExecutionCreatedEvent(DomainEvent):
    graph_node_link_execution_id: GraphNodeLinkExecutionId
    graph_execution_id: GraphExecutionId
    graph_node_execution_id: GraphNodeExecutionId

    @classmethod
    def now(
        cls,
        graph_node_link_execution_id: GraphNodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        graph_node_execution_id: GraphNodeExecutionId,
        now: CreatedAt,
    ) -> GraphNodeLinkExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_node_link_execution_id=graph_node_link_execution_id,
            graph_execution_id=graph_execution_id,
            graph_node_execution_id=graph_node_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            graph_node_link_execution_id=GraphNodeLinkExecutionId(
                payload.get("graph_node_link_execution_id", "")
            ),
            graph_execution_id=GraphExecutionId(payload.get("graph_execution_id", "")),
            graph_node_execution_id=GraphNodeExecutionId(
                payload.get("graph_node_execution_id", "")
            ),
        )
