"""SQL ORM model <-> domain entity mappers for GraphExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.graph_execution import GraphExecution
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_definition_id_ref import (
    GraphDefinitionIdRef,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_depth import (
    GraphDepth,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.execution_service.domain.execution.aggregates.graph_execution.value_objects.max_subgraph_depth import (
    MaxSubgraphDepth,
)
from shell.execution_service.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.platform.domain.value_objects.changed_at import ChangedAt
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)

if TYPE_CHECKING:
    from shell.execution_service.infrastructure.execution.graph_execution.persistence.sql.models.graph_execution import (
        GraphExecutionModel,
    )


def graph_execution_model_to_entity(graph_execution_model: GraphExecutionModel) -> GraphExecution:
    return GraphExecution.restore(
        id=GraphExecutionId(graph_execution_model.id),
        task_execution_id=TaskExecutionId(graph_execution_model.task_execution_id),
        parent_graph_execution_id=(
            GraphExecutionId(graph_execution_model.parent_graph_execution_id)
            if graph_execution_model.parent_graph_execution_id
            else None
        ),
        depth=GraphDepth(graph_execution_model.depth),
        max_subgraph_depth=MaxSubgraphDepth(graph_execution_model.max_subgraph_depth),
        graph_definition_id=GraphDefinitionIdRef(graph_execution_model.graph_definition_id)
        if graph_execution_model.graph_definition_id
        else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(graph_execution_model.created_at)),
        changed_at=ChangedAt.from_datetime(_ensure_utc(graph_execution_model.changed_at)),
        deleted_at=(DeletedAt.from_datetime(graph_execution_model.deleted_at)),
    )
