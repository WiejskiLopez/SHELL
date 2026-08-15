from __future__ import annotations

from shell.execution_service.domain.execution.aggregates.user_execution import UserExecution
from shell.execution_service.domain.execution.aggregates.user_execution.repositories.user_execution_repository import (
    UserExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
    UserExecutionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemoryUserExecutionRepository(
    InMemoryRepository[UserExecution, UserExecutionId], UserExecutionRepository
):
    pass
