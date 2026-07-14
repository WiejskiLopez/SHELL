"""SQL ORM model <-> domain entity mappers for GraphExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ._created_at_value import _created_at_value

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
        GraphExecutionModel,
    )


def graph_execution_update_model(model: GraphExecutionModel, entity: GraphExecution) -> None:
    model.status = entity.status.value if hasattr(entity.status, "value") else str(entity.status)
    model.parent_graph_execution_id = (
        entity.parent_graph_execution_id.value if entity.parent_graph_execution_id else None
    )
    model.depth = entity.depth.value
    model.graph_definition_id = entity.graph_definition_id.value
    model.updated_at = entity.updated_at.value if entity.updated_at else None
    model.deleted_at = _created_at_value(entity.deleted_at)
