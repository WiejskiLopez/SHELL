from __future__ import annotations

from shell.domain.definition.aggregates.node_definition.node_definition import NodeDefinition
from shell.domain.definition.aggregates.node_definition.value_objects.max_step import MaxStep
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_type import NodeType
from shell.infrastructure.definition.node_definition.persistence.sql.models import (
    NodeDefinitionModel,
)


def node_definition_model_to_entity(
    node_definition_model: NodeDefinitionModel,
) -> NodeDefinition:
    return NodeDefinition.restore(
        id=NodeDefinitionId(node_definition_model.id),
        node_type=NodeType(node_definition_model.node_type),
        max_step=MaxStep(node_definition_model.max_step)
        if node_definition_model.max_step is not None
        else None,
    )

