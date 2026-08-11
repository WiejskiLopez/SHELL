"""SQL ORM model <-> domain entity mappers for GraphExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
    GraphExecutionModel,
)
from shell.platform.infrastructure.context import get_correlation_id

from ._created_at_value import _created_at_value

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.graph_execution import GraphExecution


def graph_execution_entity_to_model(graph_execution: GraphExecution) -> GraphExecutionModel:
    return GraphExecutionModel(
        id=graph_execution.id.value,
        task_execution_id=graph_execution.task_execution_id.value,
        graph_definition_id=graph_execution.graph_definition_id.value,
        status=graph_execution.status.value,
        parent_graph_execution_id=(
            graph_execution.parent_graph_execution_id.value
            if graph_execution.parent_graph_execution_id
            else None
        ),
        state_input={},
        state_output={},
        depth=graph_execution.depth.value if graph_execution.depth else 0,
        max_subgraph_depth=graph_execution.max_subgraph_depth.value
        if graph_execution.max_subgraph_depth
        else 5,
        timeout_at=None,
        correlation_id=get_correlation_id(),
        tags={},
        created_at=graph_execution.created_at.value if graph_execution.created_at else None,
        updated_at=graph_execution.updated_at.value,
        deleted_at=_created_at_value(graph_execution.deleted_at),
    )
