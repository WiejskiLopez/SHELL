from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_link_definition.node_link_definition import (
    NodeLinkDefinition,
)
from shell.domain.definition.aggregates.node_link_definition.value_objects.node_link_definition_id import (
    NodeLinkDefinitionId,
)

if TYPE_CHECKING:
    from shell.infrastructure.definition.node_link_definition.persistence.sql.models import (
        NodeLinkDefinitionModel,
    )


def node_link_definition_model_to_entity(model: NodeLinkDefinitionModel) -> NodeLinkDefinition:
    return NodeLinkDefinition.restore(
        id=NodeLinkDefinitionId(model.id),
        graph_definition_id=GraphDefinitionId(model.graph_definition_id),
        node_definition_id=NodeDefinitionId(model.node_definition_id),
    )

