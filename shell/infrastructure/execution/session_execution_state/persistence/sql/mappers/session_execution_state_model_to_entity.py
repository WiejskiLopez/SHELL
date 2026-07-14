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

