from __future__ import annotations

from typing import TYPE_CHECKING

from shell.execution_service.domain.execution.aggregates.session_execution import SessionExecution
from shell.execution_service.domain.execution.aggregates.session_execution.repositories.session_execution_repository import (
    SessionExecutionRepository,
)
from shell.execution_service.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,
)
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.execution_service.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )


class InMemorySessionExecutionRepository(
    InMemoryRepository[SessionExecution, SessionExecutionId], SessionExecutionRepository
):
    async def get_by_user_execution_id(
        self, user_execution_id: UserExecutionId
    ) -> list[SessionExecution]:
        return [se for se in self._store.values() if se.user_execution_id == user_execution_id]
