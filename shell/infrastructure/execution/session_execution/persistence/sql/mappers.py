"""SQL ORM model <-> domain entity mappers for SessionExecution aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.session_execution.session_execution import SessionExecution
from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.platform.value_objects.created_at import CreatedAt
from shell.infrastructure.execution.session_execution.persistence.sql.models.session_execution import (
    SessionExecutionModel,
)


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def session_execution_model_to_entity(model: SessionExecutionModel) -> SessionExecution:
    return SessionExecution.restore(
        id=SessionExecutionId(model.id),
        user_execution_id=(
            UserExecutionId(model.user_execution_id) if model.user_execution_id else None
        ),
        session_id=SessionIdRef(model.session_id) if model.session_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def session_execution_entity_to_model(entity: SessionExecution) -> SessionExecutionModel:
    return SessionExecutionModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value if entity.user_execution_id else None,
        session_id=entity.session_id.value if entity.session_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )


def session_execution_update_model(model: SessionExecutionModel, entity: SessionExecution) -> None:
    model.user_execution_id = entity.user_execution_id.value if entity.user_execution_id else None
    model.session_id = entity.session_id.value if entity.session_id else None
    assert entity.created_at is not None
    model.created_at = entity.created_at.value
