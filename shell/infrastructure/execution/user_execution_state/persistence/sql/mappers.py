"""SQL ORM model <-> domain entity mappers for UserExecutionState aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.execution.aggregates.user_execution_state.user_execution_state import (
    UserExecutionState,
)
from shell.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id import (
    UserExecutionStateId,
)
from shell.infrastructure.execution.user_execution_state.persistence.sql.models.user_execution_state import (
    UserExecutionStateModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def user_execution_state_model_to_entity(model: UserExecutionStateModel) -> UserExecutionState:
    return UserExecutionState.restore(
        id=UserExecutionStateId(model.id),
        user_execution_id=UserExecutionId(model.user_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)) if model.state_data else StateData({}),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_execution_state_entity_to_model(entity: UserExecutionState) -> UserExecutionStateModel:
    return UserExecutionStateModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )
