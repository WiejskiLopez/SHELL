"""SQL ORM model <-> domain entity mappers for SessionState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.deleted_at import DeletedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)
from shell.platform.types import JsonStr
from shell.session_service.domain.session.aggregates.session.value_objects.session_id import (
    SessionId,
)
from shell.session_service.domain.session.aggregates.session_state.session_state import SessionState
from shell.session_service.domain.session.aggregates.session_state.value_objects.session_state_id import (
    SessionStateId,
)

if TYPE_CHECKING:
    from shell.session_service.infrastructure.session.session_state.persistence.sql.models.session_state import (
        SessionStateModel,
    )


def session_state_model_to_entity(model: SessionStateModel) -> SessionState:
    return SessionState.restore(
        id=SessionStateId(model.id),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
        deleted_at=DeletedAt.from_datetime(_ensure_utc(model.deleted_at)),
        session_id=SessionId(model.session_id),
        direction=StateDirection(model.direction),
        state_data=StateData(JsonStr(json.dumps(dict(model.state_data))))
        if model.state_data
        else StateData(JsonStr("{}")),
    )
