from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.definition.value_objects.node_position import NodePosition
    from shell.domain.definition.value_objects.node_role_name import NodeRoleName
    from shell.domain.definition.value_objects.node_type_name import NodeTypeName


@dataclass(frozen=True, slots=True)
class GraphNodeDefinitionCreatedEvent(DomainEvent):
    graph_node_definition_id: GraphNodeDefinitionId
    graph_definition_id: GraphDefinitionId
    position: NodePosition
    role: NodeRoleName
    node_type: NodeTypeName

    @classmethod
    def now(
        cls,
        graph_node_definition_id: GraphNodeDefinitionId,
        graph_definition_id: GraphDefinitionId,
        position: NodePosition,
        role: NodeRoleName,
        node_type: NodeTypeName,
        now: datetime,
    ) -> GraphNodeDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_node_definition_id=graph_node_definition_id,
            graph_definition_id=graph_definition_id,
            position=position,
            role=role,
            node_type=node_type,
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
        from shell.domain.definition.value_objects.node_position import NodePosition
        from shell.domain.definition.value_objects.node_role_name import NodeRoleName
        from shell.domain.definition.value_objects.node_type_name import NodeTypeName

        return cls(
            occurred_at=occurred_at,
            schema_version=schema_version,
            graph_node_definition_id=GraphNodeDefinitionId(payload.get("graph_node_definition_id", "")),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            position=NodePosition(payload.get("position", 0)),
            role=NodeRoleName(payload.get("role", "")),
            node_type=NodeTypeName(payload.get("node_type", "")),
        )
