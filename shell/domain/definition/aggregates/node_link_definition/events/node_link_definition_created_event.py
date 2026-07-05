from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from shell.domain.platform.events import DomainEvent

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
        GraphDefinitionId,
    )
    from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
        NodeDefinitionId,
    )
    from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
        NodeLinkDefinitionId,
    )
    from shell.domain.platform.value_objects.created_at import CreatedAt


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
