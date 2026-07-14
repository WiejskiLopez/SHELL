"""SQL ORM model <-> domain entity mappers for TaskExecutionState aggregate."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.execution.aggregates.task_execution.value_objects.task_execution_id import (
    TaskExecutionId,
)
from shell.domain.execution.aggregates.task_execution_state.task_execution_state import (
    TaskExecutionState,
)
from shell.domain.execution.aggregates.task_execution_state.value_objects.task_execution_state_id import (
    TaskExecutionStateId,
)
from shell.infrastructure.execution.task_execution_state.persistence.sql.models.task_execution_state import (
    TaskExecutionStateModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

