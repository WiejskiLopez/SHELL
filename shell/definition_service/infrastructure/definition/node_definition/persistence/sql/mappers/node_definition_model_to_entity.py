from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition_service.domain.definition.aggregates.node_definition.node_definition import (
    NodeDefinition,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.max_step import (
    MaxStep,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_definition_id import (
    NodeDefinitionId,
)
from shell.definition_service.domain.definition.aggregates.node_definition.value_objects.node_type import (
    NodeType,
)
from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt

if TYPE_CHECKING:
    from shell.definition_service.infrastructure.definition.node_definition.persistence.sql.models import (
        NodeDefinitionModel,
    )


def node_definition_model_to_entity(
    node_definition_model: NodeDefinitionModel,
) -> NodeDefinition:
    return NodeDefinition.restore(
        id=NodeDefinitionId(node_definition_model.id),
        created_at=CreatedAt.from_datetime(node_definition_model.created_at),
        changed_at=ChangedAt.from_datetime(node_definition_model.changed_at),
        deleted_at=DeletedAt.from_datetime(node_definition_model.deleted_at),
        node_type=NodeType(node_definition_model.node_type),
        max_step=MaxStep(node_definition_model.max_step)
        if node_definition_model.max_step is not None
        else None,
    )
