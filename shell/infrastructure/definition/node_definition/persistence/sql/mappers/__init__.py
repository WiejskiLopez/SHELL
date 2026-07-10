from __future__ import annotations

from shell.domain.definition.aggregates.node_definition.node_definition import NodeDefinition
from shell.domain.definition.aggregates.node_definition.value_objects.max_step import MaxStep
from shell.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_role_name import (
    NodeRoleName,
)
from shell.domain.definition.aggregates.node_definition.value_objects.node_type_name import (
    NodeTypeName,
)
from shell.infrastructure.definition.node_definition.persistence.sql.models import (
    NodeDefinitionModel,
)
from shell.platform.domain.value_objects.mode import Mode


def node_definition_model_to_entity(
    node_definition_model: NodeDefinitionModel,
) -> NodeDefinition:
    return NodeDefinition(
        id=NodeDefinitionId(node_definition_model.id),
        mode=Mode(str(node_definition_model.mode)),
        role=NodeRoleName(node_definition_model.role),
        node_type=NodeTypeName(node_definition_model.node_type),
        max_step=MaxStep(node_definition_model.max_step)
        if node_definition_model.max_step is not None
        else None,
    )


def node_definition_entity_to_model(
    node_definition: NodeDefinition,
) -> NodeDefinitionModel:
    return NodeDefinitionModel(
        id=node_definition.id.value,
        mode=node_definition.mode.value,
        role=node_definition.role.value,
        node_type=node_definition.node_type.value,
        max_step=(
            node_definition.max_step.value if node_definition.max_step is not None else None
        ),
    )


def node_definition_update_model(model: NodeDefinitionModel, entity: NodeDefinition) -> None:
    model.mode = entity.mode.value
    model.role = entity.role.value
    model.node_type = entity.node_type.value
    model.max_step = entity.max_step.value if entity.max_step is not None else None
