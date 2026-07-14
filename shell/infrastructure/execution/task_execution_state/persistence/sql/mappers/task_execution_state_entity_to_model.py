"""SQL ORM model <-> domain entity mappers for TaskExecutionState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.infrastructure.execution.task_execution_state.persistence.sql.models.task_execution_state import (
    TaskExecutionStateModel,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
        TaskExecutionState,
    )


def task_execution_state_entity_to_model(entity: TaskExecutionState) -> TaskExecutionStateModel:
    return TaskExecutionStateModel(
        id=entity.id.value,
        task_execution_id=entity.task_execution_id.value,
        direction=entity.direction.value,
        state_data=json.dumps(json.loads(entity.state_data.value.value)),
        created_at=entity.created_at.value if entity.created_at else None,
    )
