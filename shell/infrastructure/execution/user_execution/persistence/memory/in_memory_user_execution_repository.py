from __future__ import annotations

from shell.domain.execution.aggregates.user_execution import UserExecution
from shell.domain.execution.aggregates.user_execution.repositories.user_execution_repository import (
    UserExecutionRepository,
)
from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemoryUserExecutionRepository(
    InMemoryRepository[UserExecution, UserExecutionId], UserExecutionRepository
):
    pass
