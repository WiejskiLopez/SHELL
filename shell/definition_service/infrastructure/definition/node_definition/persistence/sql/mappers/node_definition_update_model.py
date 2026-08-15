from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.node_definition.node_definition import (
        NodeDefinition,
    )
    from shell.definition_service.infrastructure.definition.node_definition.persistence.sql.models import (
        NodeDefinitionModel,
    )


def node_definition_update_model(model: NodeDefinitionModel, entity: NodeDefinition) -> None:
    model.node_type = entity.node_type.value
    model.max_step = entity.max_step.value if entity.max_step is not None else None
