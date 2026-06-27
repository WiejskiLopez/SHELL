from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionAttachedEvent(DomainEvent):
    graph_execution_id: GraphExecutionId
    graph_node_definition_id: GraphNodeDefinitionId
    graph_node_execution_id: GraphNodeExecutionId

    @classmethod
    def now(
        cls,
        graph_execution_id: GraphExecutionId,
        graph_node_definition_id: GraphNodeDefinitionId,
        graph_node_execution_id: GraphNodeExecutionId,
        now: datetime,
    ) -> GraphNodeExecutionAttachedEvent:
        return cls(
            occurred_at=now,
            graph_execution_id=graph_execution_id,
            graph_node_definition_id=graph_node_definition_id,
            graph_node_execution_id=graph_node_execution_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_execution_id=GraphExecutionId(payload["graph_execution_id"]),
            graph_node_definition_id=GraphNodeDefinitionId(payload["graph_node_definition_id"]),
            graph_node_execution_id=GraphNodeExecutionId(payload["graph_node_execution_id"]),
        )
