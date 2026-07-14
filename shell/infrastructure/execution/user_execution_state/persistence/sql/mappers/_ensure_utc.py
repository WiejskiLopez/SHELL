"""SQL ORM model <-> domain entity mappers for UserExecutionState aggregate."""

from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.execution.aggregates.user_execution_state.user_execution_state import (
    UserExecutionState,
)
from shell.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id import (
    UserExecutionStateId,
)
from shell.infrastructure.execution.user_execution_state.persistence.sql.models.user_execution_state import (
    UserExecutionStateModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.domain.value_objects.state_data import StateData
from shell.platform.domain.value_objects.state_direction import StateDirection
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

