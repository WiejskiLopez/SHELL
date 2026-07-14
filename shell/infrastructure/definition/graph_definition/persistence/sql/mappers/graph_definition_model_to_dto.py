from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.definition.graph_definition.dto.graph_definition import GraphDefinitionDto

if TYPE_CHECKING:
    from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
        GraphDefinitionModel,
    )


def graph_definition_model_to_dto(model: GraphDefinitionModel) -> GraphDefinitionDto:
    return GraphDefinitionDto(
        id=model.id,
        node_definitions=[],
    )
