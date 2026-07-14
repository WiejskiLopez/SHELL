"""SQL ORM model <-> domain entity mappers for UserExecution aggregate."""

from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_id_ref import UserIdRef
from shell.infrastructure.execution.user_execution.persistence.sql.models.user_execution import (
    UserExecutionModel,
)
from shell.platform.domain.value_objects.created_at import CreatedAt


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt

