from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.edge_execution.edge_execution import EdgeExecution
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_definition_id import (
    EdgeDefinitionId,
)
from shell.domain.execution.aggregates.edge_execution.value_objects.edge_execution_id import (
    EdgeExecutionId,
)
from shell.domain.execution.aggregates.node_execution.value_objects.node_execution_id import (
    NodeExecutionId,
)
from shell.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
    EdgeExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.updated_at import UpdatedAt


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def edge_execution_model_to_entity(model: EdgeExecutionModel) -> EdgeExecution:
    return EdgeExecution.restore(
        id_=EdgeExecutionId(model.id),
        edge_definition_id=EdgeDefinitionId(model.edge_definition_id),
        source_node_execution_id=NodeExecutionId(model.source_node_execution_id),
        target_node_execution_id=(
            NodeExecutionId(model.target_node_execution_id)
            if model.target_node_execution_id
            else None
        ),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        updated_at=UpdatedAt.from_datetime(_ensure_utc(model.updated_at)),
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at))
        if model.deleted_at is not None
        else None,
    )


def edge_execution_entity_to_model(
    entity: EdgeExecution,
    now: datetime,
) -> EdgeExecutionModel:
    return EdgeExecutionModel(
        id=entity.id.value,
        edge_definition_id=entity.edge_definition_id.value,
        source_node_execution_id=entity.source_node_execution_id.value,
        target_node_execution_id=(
            entity.target_node_execution_id.value if entity.target_node_execution_id else None
        ),
        created_at=now,
        updated_at=now,
    )


def edge_execution_update_model(
    model: EdgeExecutionModel,
    entity: EdgeExecution,
    now: datetime,
) -> None:
    model.edge_definition_id = entity.edge_definition_id.value
    model.source_node_execution_id = entity.source_node_execution_id.value
    model.target_node_execution_id = (
        entity.target_node_execution_id.value if entity.target_node_execution_id else None
    )
    model.updated_at = now
