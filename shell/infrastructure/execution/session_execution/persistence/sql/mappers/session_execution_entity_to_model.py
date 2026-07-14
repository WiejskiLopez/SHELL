"""SQL ORM model <-> domain entity mappers for SessionExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.execution.session_execution.persistence.sql.models.session_execution import (
    SessionExecutionModel,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.session_execution import (
        SessionExecution,
    )


def session_execution_entity_to_model(entity: SessionExecution) -> SessionExecutionModel:
    return SessionExecutionModel(
        id=entity.id.value,
        user_execution_id=entity.user_execution_id.value if entity.user_execution_id else None,
        session_id=entity.session_id.value if entity.session_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )

