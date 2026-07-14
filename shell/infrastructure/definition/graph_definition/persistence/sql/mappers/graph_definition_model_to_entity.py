from __future__ import annotations

from shell.application.definition.graph_definition.dto.graph_definition import GraphDefinitionDto
from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
    GraphDefinitionModel,
)


def graph_definition_model_to_entity(model: GraphDefinitionModel) -> GraphDefinition:
    return GraphDefinition.restore(
        id=GraphDefinitionId(model.id),
    )

