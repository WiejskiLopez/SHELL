"""SQL ORM model <-> domain entity mappers for UserExecutionState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.execution.infrastructure.execution.user_execution_state.persistence.sql.models.user_execution_state import (
    UserExecutionStateModel,
)

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.user_execution_state.user_execution_state import (
        UserExecutionState,
    )


def user_execution_state_entity_to_model(entity: UserExecutionState) -> UserExecutionStateModel:
    return UserExecutionStateModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value,
        direction=entity.direction.value,
        state_data=json.dumps(json.loads(entity.state_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
    )
