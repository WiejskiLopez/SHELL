from __future__ import annotations

from typing import TYPE_CHECKING

from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.models import (
    GraphDefinitionModel,
)

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.graph_definition.graph_definition import (
        GraphDefinition,
    )


def graph_definition_entity_to_model(entity: GraphDefinition) -> GraphDefinitionModel:
    return GraphDefinitionModel(
        id=str(entity.id.value),
        created_at=entity.created_at.value,
    )
