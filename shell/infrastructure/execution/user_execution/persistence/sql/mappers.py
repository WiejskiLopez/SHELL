"""SQL ORM model <-> domain entity mappers for UserExecution aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution
from shell.domain.execution.value_objects.ids import UserExecutionId
from shell.domain.execution.value_objects.user_id_ref import UserIdRef
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.execution.user_execution.persistence.sql.models.user_execution import (
    UserExecutionModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def user_execution_model_to_entity(model: UserExecutionModel) -> UserExecution:
    return UserExecution.restore(
        id=UserExecutionId(model.id),
        user_id=UserIdRef(model.user_id) if model.user_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def user_execution_entity_to_model(entity: UserExecution) -> UserExecutionModel:
    return UserExecutionModel(
        id=entity.id.value,
        user_id=entity.user_id.value if entity.user_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )


def user_execution_update_model(model: UserExecutionModel, entity: UserExecution) -> None:
    model.user_id = entity.user_id.value if entity.user_id else None
    assert entity.created_at is not None
    model.created_at = entity.created_at.value
