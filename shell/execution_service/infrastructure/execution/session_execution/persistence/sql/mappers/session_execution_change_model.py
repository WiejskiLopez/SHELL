"""SQL ORM model <-> domain entity mappers for SessionExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.session_execution.session_execution import (
        SessionExecution,
    )
    from shell.execution_service.infrastructure.execution.session_execution.persistence.sql.models.session_execution import (
        SessionExecutionModel,
    )


def session_execution_change_model(model: SessionExecutionModel, entity: SessionExecution) -> None:
    model.user_execution_id = entity.user_execution_id.value if entity.user_execution_id else None
    model.session_id = entity.session_id.value if entity.session_id else None
    assert entity.created_at is not None
    model.created_at = entity.created_at.value
