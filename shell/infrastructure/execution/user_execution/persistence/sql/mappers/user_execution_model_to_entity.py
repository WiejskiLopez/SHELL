"""SQL ORM model <-> domain entity mappers for UserExecution aggregate."""

from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_id_ref import UserIdRef
from shell.platform.domain.value_objects.created_at import CreatedAt

from ._ensure_utc import _ensure_utc

if TYPE_CHECKING:
    from shell.infrastructure.execution.user_execution.persistence.sql.models.user_execution import (
        UserExecutionModel,
    )


def user_execution_model_to_entity(model: UserExecutionModel) -> UserExecution:
    return UserExecution.restore(
        id=UserExecutionId(model.id),
        user_id=UserIdRef(model.user_id) if model.user_id else None,
        created_at=CreatedAt.from_datetime(_ensure_utc(model.created_at)),
    )

