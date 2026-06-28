from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.edge_type import EdgeType

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
        GraphNodeTransitionDefinitionId,
    )


@dataclass(frozen=True, slots=True)
class GraphNodeTransitionDefinitionCreatedEvent(DomainEvent):
    graph_node_transition_definition_id: GraphNodeTransitionDefinitionId
    graph_definition_id: GraphDefinitionId
    source_node_definition_id: GraphNodeDefinitionId | None
    target_node_definition_id: GraphNodeDefinitionId
    transition_type: EdgeType

    @classmethod
    def now(
        cls,
        graph_node_transition_definition_id: GraphNodeTransitionDefinitionId,
        graph_definition_id: GraphDefinitionId,
        source_node_definition_id: GraphNodeDefinitionId | None,
        target_node_definition_id: GraphNodeDefinitionId,
        transition_type: EdgeType,
        now: datetime,
    ) -> GraphNodeTransitionDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_node_transition_definition_id=graph_node_transition_definition_id,
            graph_definition_id=graph_definition_id,
            source_node_definition_id=source_node_definition_id,
            target_node_definition_id=target_node_definition_id,
            transition_type=transition_type,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
            GraphDefinitionId,
        )
        from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
            GraphNodeDefinitionId,
        )
        from shell.domain.definition.aggregates.graph_node_transition_definition.value_objects.graph_node_transition_definition_id import (
            GraphNodeTransitionDefinitionId,
        )

        source_id = payload.get("source_node_definition_id")
        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_transition_definition_id=GraphNodeTransitionDefinitionId(payload.get("graph_node_transition_definition_id", "")),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            source_node_definition_id=GraphNodeDefinitionId(source_id) if source_id else None,
            target_node_definition_id=GraphNodeDefinitionId(payload.get("target_node_definition_id", "")),
            transition_type=EdgeType(payload.get("transition_type", "")),
        )
