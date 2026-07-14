"""SQL ORM model <-> domain entity mappers for GraphExecution aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution import GraphExecution
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_depth import GraphDepth
from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
    GraphExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt
from shell.platform.infrastructure.context import get_correlation_id


def graph_execution_entity_to_model(graph_execution: GraphExecution) -> GraphExecutionModel:
    return GraphExecutionModel(
        id=graph_execution.id.value,
        task_execution_id=graph_execution.task_execution_id.value,
        graph_definition_id=graph_execution.graph_definition_id.value,
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
        updated_at=graph_execution.updated_at.value if graph_execution.updated_at else None,
        deleted_at=_created_at_value(graph_execution.deleted_at),
    )