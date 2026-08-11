"""SQL ORM model <-> domain entity mappers for TaskExecutionState aggregate."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.execution.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.execution.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
    TaskExecutionStateId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime

if TYPE_CHECKING:
    from shell.execution.infrastructure.execution.task_execution_state.persistence.sql.models.task_execution_state import (
        TaskExecutionStateModel,
    )


def task_execution_state_model_to_entity(model: TaskExecutionStateModel) -> TaskExecutionState:
    return TaskExecutionState.restore(
        id=TaskExecutionStateId(model.id),
        task_execution_id=TaskExecutionId(model.task_execution_id),
        direction=StateDirection(model.direction),
        state_data=StateData(JsonStr(json.dumps(dict(model.state_data)))),
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )
