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


def user_execution_entity_to_model(entity: UserExecution) -> UserExecutionModel:
    return UserExecutionModel(
        id=entity.id.value,
        user_id=entity.user_id.value if entity.user_id else None,
        created_at=entity.created_at.value if entity.created_at else None,
    )

