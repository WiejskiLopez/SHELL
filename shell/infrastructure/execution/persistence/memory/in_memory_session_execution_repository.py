from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.session_execution.repositories.session_execution_repository import (
    SessionExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (  # noqa: TC002 — SessionExecutionId, UserExecutionId używane w konstruktorach w repozytorium
    SessionExecutionId,
    UserExecutionId,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution import SessionExecution


class InMemorySessionExecutionRepository(SessionExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, SessionExecution] = {}

    async def get_by_id(self, id: SessionExecutionId) -> SessionExecution | None:
        return self._store.get(id.value)

    async def get_by_user_execution_id(
        self, user_execution_id: UserExecutionId
    ) -> list[SessionExecution]:
        return [
            se
            for se in self._store.values()
            if se.user_execution_id == user_execution_id
        ]

    async def save(self, session_execution: SessionExecution) -> None:
        self._store[session_execution.id.value] = session_execution

    async def delete(self, id: SessionExecutionId) -> None:
        self._store.pop(id.value, None)

    async def exists(self, id: SessionExecutionId) -> bool:
        return id.value in self._store
