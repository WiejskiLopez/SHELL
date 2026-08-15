from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition_service.infrastructure.definition.node_definition.persistence.sql.models import (
    NodeDefinitionModel,
)

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.node_definition.node_definition import (
        NodeDefinition,
    )


def node_definition_entity_to_model(
    node_definition: NodeDefinition,
) -> NodeDefinitionModel:
    return NodeDefinitionModel(
        id=node_definition.id.value,
        node_type=node_definition.node_type.value,
        max_step=(node_definition.max_step.value if node_definition.max_step is not None else None),
    )
