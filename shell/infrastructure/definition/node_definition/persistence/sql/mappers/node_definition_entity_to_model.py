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


def node_definition_entity_to_model(
    node_definition: NodeDefinition,
) -> NodeDefinitionModel:
    return NodeDefinitionModel(
        id=node_definition.id.value,
        node_type=node_definition.node_type.value,
        max_step=(
            node_definition.max_step.value if node_definition.max_step is not None else None
        ),
    )

