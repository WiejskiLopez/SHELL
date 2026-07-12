from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
    GraphDefinitionModel,
)


def graph_definition_model_to_entity(
    graph_definition_model: GraphDefinitionModel,
) -> GraphDefinition:
    return GraphDefinition.restore(
        id=GraphDefinitionId(graph_definition_model.id),
    )


def graph_definition_entity_to_model(
    graph_definition: GraphDefinition,
) -> GraphDefinitionModel:
    return GraphDefinitionModel(
        id=str(graph_definition.id.value),
    )


def graph_definition_update_model(model: GraphDefinitionModel, entity: GraphDefinition) -> None:
    pass
