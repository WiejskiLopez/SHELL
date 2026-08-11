from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition.infrastructure.definition.node_link_definition.persistence.sql.models import (
    NodeLinkDefinitionModel,
)

if TYPE_CHECKING:
    from shell.definition.domain.definition.aggregates.node_link_definition.node_link_definition import (
        NodeLinkDefinition,
    )


def node_link_definition_entity_to_model(entity: NodeLinkDefinition) -> NodeLinkDefinitionModel:
    return NodeLinkDefinitionModel(
        id=entity.id.value,
        graph_definition_id=entity.graph_definition_id.value,
        node_definition_id=entity.node_definition_id.value,
    )
