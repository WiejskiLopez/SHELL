from __future__ import annotations

from shell.domain.execution.aggregates.session_execution import SessionExecution
from shell.domain.execution.aggregates.session_execution.repositories.session_execution_repository import (
    SessionExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (
    SessionExecutionId,
    UserExecutionId,
)
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository


class InMemorySessionExecutionRepository(
    InMemoryRepository[SessionExecution, SessionExecutionId], SessionExecutionRepository
):
    async def get_by_user_execution_id(
        self, user_execution_id: UserExecutionId
    ) -> list[SessionExecution]:
        return [se for se in self._store.values() if se.user_execution_id == user_execution_id]
