"""SQL ORM model <-> domain entity mappers for UserExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.user_execution.user_execution import (
        UserExecution,
    )
    from shell.execution_service.infrastructure.execution.user_execution.persistence.sql.models.user_execution import (
        UserExecutionModel,
    )


def user_execution_change_model(model: UserExecutionModel, entity: UserExecution) -> None:
    model.user_id = entity.user_id.value if entity.user_id else None
    assert entity.created_at is not None
    model.created_at = entity.created_at.value
