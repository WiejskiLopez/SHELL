from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.domain.execution.value_objects.node_definition_id import NodeDefinitionId
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion


@dataclass(frozen=True, slots=True)
class NodeExecutionAttachedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    node_definition_id: NodeDefinitionId
    node_execution_id: NodeExecutionId

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        node_definition_id: NodeDefinitionId,
        node_execution_id: NodeExecutionId,
        now: CreatedAt,
    ) -> NodeExecutionAttachedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            node_definition_id=node_definition_id,
            node_execution_id=node_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            node_definition_id=NodeDefinitionId(payload["node_definition_id"]),
            node_execution_id=NodeExecutionId(payload["node_execution_id"]),
        )
