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


def node_definition_update_model(model: NodeDefinitionModel, entity: NodeDefinition) -> None:
    model.node_type = entity.node_type.value
    model.max_step = entity.max_step.value if entity.max_step is not None else None