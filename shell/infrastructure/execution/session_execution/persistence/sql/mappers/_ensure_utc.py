"""SQL ORM model <-> domain entity mappers for SessionExecution aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.session_execution.session_execution import SessionExecution
from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.infrastructure.execution.session_execution.persistence.sql.models.session_execution import (
    SessionExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

