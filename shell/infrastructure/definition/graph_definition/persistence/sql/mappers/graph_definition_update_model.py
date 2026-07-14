from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)
from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
    GraphDefinitionModel,
)


def graph_definition_update_model(model: GraphDefinitionModel, entity: GraphDefinition) -> None:
    pass