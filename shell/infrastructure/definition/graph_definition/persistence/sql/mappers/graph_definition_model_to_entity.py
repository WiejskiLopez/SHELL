from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
from shell.domain.definition.aggregates.graph_definition.value_objects.graph_definition_id import (
    GraphDefinitionId,
)

if TYPE_CHECKING:
    from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
        GraphDefinitionModel,
    )


def graph_definition_model_to_entity(model: GraphDefinitionModel) -> GraphDefinition:
    return GraphDefinition.restore(
        id=GraphDefinitionId(model.id),
    )

