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


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def _created_at_value(dt: CreatedAt | DeletedAt | datetime | None) -> datetime | None:
    if dt is None:
        return None
    return dt.value if hasattr(dt, "value") else dt


def graph_execution_model_to_entity(graph_execution_model: GraphExecutionModel) -> GraphExecution:
    return GraphExecution(
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
        created_at=CreatedAt.from_datetime(_ensure_utc(graph_execution_model.created_at))
        if graph_execution_model.created_at
        else None,
        updated_at=UpdatedAt.from_datetime(_ensure_utc(graph_execution_model.updated_at))
        if graph_execution_model.updated_at
        else None,
        deleted_at=(
            DeletedAt.from_datetime(graph_execution_model.deleted_at)
            if graph_execution_model.deleted_at
            else None
        ),
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
