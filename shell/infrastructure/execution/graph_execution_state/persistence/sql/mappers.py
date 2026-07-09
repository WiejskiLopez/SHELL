"""SQL ORM model <-> domain entity mappers for GraphExecutionState aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.graph_execution.value_objects.graph_execution_id import (
    GraphExecutionId,
)
from shell.domain.execution.aggregates.graph_execution_state.graph_execution_state import (
    GraphExecutionState,
)
from shell.domain.execution.aggregates.graph_execution_state.value_objects.graph_execution_state_id import (
    GraphExecutionStateId,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state_input import (
    GraphExecutionStateInputModel,
)
from shell.infrastructure.execution.graph_execution_state.persistence.sql.models.graph_execution_state_output import (
    GraphExecutionStateOutputModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def graph_execution_state_input_model_to_entity(
    model: GraphExecutionStateInputModel,
) -> GraphExecutionState:
    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.IN,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_input_entity_to_model(
    entity: GraphExecutionState,
) -> GraphExecutionStateInputModel:
    return GraphExecutionStateInputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data,
        created_at=entity.created_at.value,
    )


def graph_execution_state_output_model_to_entity(
    model: GraphExecutionStateOutputModel,
) -> GraphExecutionState:
    return GraphExecutionState(
        id=GraphExecutionStateId(model.id),
        graph_execution_id=GraphExecutionId(model.graph_execution_id),
        direction=StateDirection.OUT,
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def graph_execution_state_output_entity_to_model(
    entity: GraphExecutionState,
) -> GraphExecutionStateOutputModel:
    return GraphExecutionStateOutputModel(
        id=entity.id.value,
        graph_execution_id=entity.graph_execution_id.value,
        state_data=entity.state_data,
        created_at=entity.created_at.value,
    )
