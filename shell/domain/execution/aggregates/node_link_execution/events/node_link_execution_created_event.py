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
    from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
        NodeExecutionId,
    )
    from shell.domain.execution.aggregates.node_link_execution.value_objects.node_link_execution_id import (
        NodeLinkExecutionId,
    )


@dataclass(frozen=True, slots=True)
class NodeLinkExecutionCreatedEvent(DomainEvent):
    node_link_execution_id: NodeLinkExecutionId
    graph_execution_id: GraphExecutionId
    node_execution_id: NodeExecutionId

    @classmethod
    def now(
        cls,
        node_link_execution_id: NodeLinkExecutionId,
        graph_execution_id: GraphExecutionId,
        node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> NodeLinkExecutionCreatedEvent:
        return cls(
            occurred_at=now,
            node_link_execution_id=node_link_execution_id,
            graph_execution_id=graph_execution_id,
            node_execution_id=node_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            node_link_execution_id=NodeLinkExecutionId(
                payload.get("node_link_execution_id", "")
            ),
            graph_execution_id=GraphExecutionId(payload.get("graph_execution_id", "")),
            node_execution_id=NodeExecutionId(
                payload.get("node_execution_id", "")
            ),
        )
