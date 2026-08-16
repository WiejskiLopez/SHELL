"""SQL ORM model <-> domain entity mappers for SessionState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.session_service.infrastructure.session.session_state.persistence.sql.models.session_state import (
    SessionStateModel,
)

if TYPE_CHECKING:
    from shell.session_service.domain.session.aggregates.session_state.session_state import (
        SessionState,
    )


def session_state_entity_to_model(entity: SessionState) -> SessionStateModel:
    return SessionStateModel(
        id=entity.id.value,
        session_id=entity.session_id.value,
        direction=entity.direction.value,
        state_data=json.loads(entity.state_data.value.value),
        created_at=entity.created_at.value,
        deleted_at=entity._deleted_at.value,
    )
