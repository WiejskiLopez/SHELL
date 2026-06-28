from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

if TYPE_CHECKING:
    from datetime import datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.execution.value_objects.graph_node_definition_id import GraphNodeDefinitionId
from shell.domain.platform.events import DomainEvent


@dataclass(frozen=True, slots=True)
class GraphNodeExecutionInitializedEvent(DomainEvent):
    node_id: GraphNodeExecutionId
    graph_execution_id: GraphExecutionId
    parent_graph_execution_id: GraphExecutionId
    node_definition_id: GraphNodeDefinitionId

    @classmethod
    def now(
        cls,
        node_id: GraphNodeExecutionId,
        graph_execution_id: GraphExecutionId,
        parent_graph_execution_id: GraphExecutionId,
        node_definition_id: GraphNodeDefinitionId,
        now: datetime,
    ) -> GraphNodeExecutionInitializedEvent:
        return cls(
            occurred_at=now,
            node_id=node_id,
            graph_execution_id=graph_execution_id,
            parent_graph_execution_id=parent_graph_execution_id,
            node_definition_id=node_definition_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            node_id=GraphNodeExecutionId(payload.get("node_id")),
            graph_execution_id=GraphExecutionId(payload.get("graph_execution_id")),
            parent_graph_execution_id=GraphExecutionId(payload.get("parent_graph_execution_id")),
            node_definition_id=GraphNodeDefinitionId(payload.get("node_definition_id")),
        )
