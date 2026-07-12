"""SQL ORM model <-> domain entity mappers for SessionExecutionState aggregate."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.execution.aggregates.session_execution_state.session_execution_state import (
    SessionExecutionState,
)
from shell.domain.execution.aggregates.session_execution_state.value_objects.session_execution_state_id import (
    SessionExecutionStateId,
)
from shell.infrastructure.execution.session_execution_state.persistence.sql.models.session_execution_state import (
    SessionExecutionStateModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt


def session_execution_state_model_to_entity(
    model: SessionExecutionStateModel,
) -> SessionExecutionState:
    return SessionExecutionState.restore(
        id=SessionExecutionStateId(model.id),
        session_execution_id=SessionExecutionId(model.session_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(JsonStr(json.dumps(dict(model.state_data)))) if model.state_data else StateData(JsonStr("{}")),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )


def session_execution_state_entity_to_model(
    entity: SessionExecutionState,
) -> SessionExecutionStateModel:
    return SessionExecutionStateModel(
        id=entity.id.value,
        session_execution_id=entity.session_execution_id.value,
        direction=entity.direction.value,
        state_data=json.dumps(json.loads(entity.state_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
    )
