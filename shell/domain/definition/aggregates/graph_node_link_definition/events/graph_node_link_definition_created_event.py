from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion

if TYPE_CHECKING:
    from datetime import datetime

    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_definition.value_objects.graph_node_definition_id import (
        GraphNodeDefinitionId,
    )
    from shell.domain.definition.aggregates.graph_node_link_definition.value_objects.graph_node_link_definition_id import (
        GraphNodeLinkDefinitionId,
    )


@dataclass(frozen=True, slots=True)
class GraphNodeLinkDefinitionCreatedEvent(DomainEvent):
    graph_node_link_definition_id: GraphNodeLinkDefinitionId
    graph_definition_id: GraphDefinitionId
    graph_node_definition_id: GraphNodeDefinitionId

    @classmethod
    def now(
        cls,
        graph_node_link_definition_id: GraphNodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        graph_node_definition_id: GraphNodeDefinitionId,
        now: CreatedAt,
    ) -> GraphNodeLinkDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            graph_node_link_definition_id=graph_node_link_definition_id,
            graph_definition_id=graph_definition_id,
            graph_node_definition_id=graph_node_definition_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            graph_node_link_definition_id=GraphNodeLinkDefinitionId(
                payload.get("graph_node_link_definition_id", "")
            ),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            graph_node_definition_id=GraphNodeDefinitionId(
                payload.get("graph_node_definition_id", "")
            ),
        )
