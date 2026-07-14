from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.domain.definition.aggregates.graph_definition.graph_definition import GraphDefinition
    from shell.infrastructure.definition.graph_definition.persistence.sql.models import (
        GraphDefinitionModel,
    )


def graph_definition_update_model(model: GraphDefinitionModel, entity: GraphDefinition) -> None:
    pass
