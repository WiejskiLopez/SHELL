"""SQL ORM model <-> domain entity mappers for SessionExecutionState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.infrastructure.execution.session_execution_state.persistence.sql.models.session_execution_state import (
    SessionExecutionStateModel,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution_state.session_execution_state import (
        SessionExecutionState,
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
