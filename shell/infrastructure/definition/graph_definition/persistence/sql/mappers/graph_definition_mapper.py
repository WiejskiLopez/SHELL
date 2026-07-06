from __future__ import annotations

from shell.application.definition.graph_definition.dto.graph_definition import GraphDefinitionDto
from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.infrastructure.definition.persistence.sql.models import (
    GraphDefinitionModel,
)


def graph_definition_model_to_dto(model: GraphDefinitionModel) -> GraphDefinitionDto:
    return GraphDefinitionDto(
        id=model.id,
        node_definitions=[],
    )


def graph_definition_model_to_entity(model: GraphDefinitionModel) -> GraphDefinition:
    return GraphDefinition(
        id=GraphDefinitionId(model.id),
    )


def graph_definition_entity_to_model(entity: GraphDefinition) -> GraphDefinitionModel:
    return GraphDefinitionModel(
        id=str(entity.id.value),
    )
