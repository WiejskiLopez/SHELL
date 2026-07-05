from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Self

from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)
from shell.domain.platform.events import DomainEvent
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.schema_version import SchemaVersion

if TYPE_CHECKING:
    from datetime import datetime



@dataclass(frozen=True, slots=True)
class NodeLinkDefinitionCreatedEvent(DomainEvent):
    node_link_definition_id: NodeLinkDefinitionId
    graph_definition_id: GraphDefinitionId
    node_definition_id: NodeDefinitionId

    @classmethod
    def now(
        cls,
        node_link_definition_id: NodeLinkDefinitionId,
        graph_definition_id: GraphDefinitionId,
        node_definition_id: NodeDefinitionId,
        now: CreatedAt,
    ) -> NodeLinkDefinitionCreatedEvent:
        return cls(
            occurred_at=now,
            node_link_definition_id=node_link_definition_id,
            graph_definition_id=graph_definition_id,
            node_definition_id=node_definition_id,
        )

    @classmethod
    def from_payload(
        cls, occurred_at: datetime, payload: dict[str, Any], schema_version: int = 1
    ) -> Self:
        return cls(
            occurred_at=CreatedAt.from_datetime(occurred_at),
            schema_version=SchemaVersion(schema_version),
            node_link_definition_id=NodeLinkDefinitionId(
                payload.get("node_link_definition_id", "")
            ),
            graph_definition_id=GraphDefinitionId(payload.get("graph_definition_id", "")),
            node_definition_id=NodeDefinitionId(
                payload.get("node_definition_id", "")
            ),
        )
