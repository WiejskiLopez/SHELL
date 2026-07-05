from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_transition_definition.value_objects.node_transition_definition_id import (
    NodeTransitionDefinitionId,
)
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.edge_type import EdgeType
from shell.domain.platform.value_objects.schema_version import SchemaVersion

if TYPE_CHECKING:
    from datetime import datetime



@dataclass(frozen=True, slots=True)
class NodeTransitionDefinitionCreatedEvent(DomainEvent):
    node_transition_definition_id: NodeTransitionDefinitionId
    graph_definition_id: GraphDefinitionId
    source_node_definition_id: NodeDefinitionId | None
    target_node_definition_id: NodeDefinitionId
    transition_type: EdgeType

    @classmethod
    def now(
        cls,
        node_transition_definition_id: NodeTransitionDefinitionId,
        graph_definition_id: GraphDefinitionId,
        source_node_definition_id: NodeDefinitionId | None,
        target_node_definition_id: NodeDefinitionId,
        transition_type: EdgeType,
        now: CreatedAt,
    ) -> NodeTransitionDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            node_transition_definition_id=node_transition_definition_id,
            graph_definition_id=graph_definition_id,
            source_node_definition_id=source_node_definition_id,
            target_node_definition_id=target_node_definition_id,
            transition_type=transition_type,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        source_id = payload["source_node_definition_id"]
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            node_transition_definition_id=NodeTransitionDefinitionId(
                payload.get("node_transition_definition_id", "")
            ),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            source_node_definition_id=NodeDefinitionId(source_id) if source_id else None,
            target_node_definition_id=NodeDefinitionId(
                payload.get("target_node_definition_id", "")
            ),
            transition_type=EdgeType(payload.get("transition_type", "")),
        )
