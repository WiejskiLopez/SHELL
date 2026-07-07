"""SQL ORM model <-> domain entity mappers for TaskExecutionState aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.value_objects.ids import TaskExecutionId, TaskExecutionStateId
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.domain.platform.value_objects.state_data import StateData
from shell.domain.platform.value_objects.state_direction import StateDirection
from shell.infrastructure.execution.task_execution_state.persistence.sql.models.task_execution_state import (
    TaskExecutionStateModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def task_execution_state_model_to_entity(model: TaskExecutionStateModel) -> TaskExecutionState:
    return TaskExecutionState(
        id=TaskExecutionStateId(model.id),
        task_execution_id=TaskExecutionId(model.task_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(dict(model.state_data)),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def task_execution_state_entity_to_model(entity: TaskExecutionState) -> TaskExecutionStateModel:
    return TaskExecutionStateModel(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        direction=entity.direction.value,
        state_data=entity.state_data.to_dict(),
        created_at=entity.created_at.value if entity.created_at else None,
    )
