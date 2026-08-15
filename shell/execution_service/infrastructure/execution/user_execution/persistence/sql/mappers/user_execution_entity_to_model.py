"""SQL ORM model <-> domain entity mappers for UserExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.infrastructure.execution.user_execution.persistence.sql.models.user_execution import (
    UserExecutionModel,
)

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.user_execution.user_execution import (
        UserExecution,
    )


def user_execution_entity_to_model(entity: UserExecution) -> UserExecutionModel:
    return UserExecutionModel(
        id=entity.id.value,
        user_id=entity.user_id.value if entity.user_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )
