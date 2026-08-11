"""SQL ORM model <-> domain entity mapper for GraphExecutionState aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state import (
    GraphExecutionStateModel,
)

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
        GraphExecutionState,
    )


def entity_to_model(entity: GraphExecutionState) -> GraphExecutionStateModel:
    return GraphExecutionStateModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data,
        created_at=entity.created_at.value,
    )
