from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.definition_service.domain.definition.aggregates.graph_definition.graph_definition import (
        GraphDefinition,
    )
    from shell.definition_service.infrastructure.definition.graph_definition.persistence.sql.models import (
        GraphDefinitionModel,
    )


def graph_definition_update_model(model: GraphDefinitionModel, entity: GraphDefinition) -> None:
    model.created_at = entity.created_at.value
