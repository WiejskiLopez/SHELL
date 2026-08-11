"""SQL ORM model <-> domain entity mappers for SessionExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution.domain.execution.aggregates.session_execution.session_execution import (
    SessionExecution,
)
from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_id_ref import (
    SessionIdRef,
)
from shell.execution.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.infrastructure.persistence.sql.mappers._ensure_utc import (
    ensure_utc as _ensure_utc,
)

if TYPE_CHECKING:
    from shell.execution.infrastructure.execution.session_execution.persistence.sql.models.session_execution import (
        SessionExecutionModel,
    )


def session_execution_model_to_entity(model: SessionExecutionModel) -> SessionExecution:
    return SessionExecution.restore(
        id=SessionExecutionId(model.id),
        user_execution_id=(
            UserExecutionId(model.user_execution_id) if model.user_execution_id else None
        ),
        session_id=SessionIdRef(model.session_id) if model.session_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )
