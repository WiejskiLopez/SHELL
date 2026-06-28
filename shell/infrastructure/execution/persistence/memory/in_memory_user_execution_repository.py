from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.user_execution.repositories.user_execution_repository import (
    UserExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (  # noqa: TC002 — UserExecutionId używany w konstruktorach w repozytorium
    UserExecutionId,
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution import UserExecution


class InMemoryUserExecutionRepository(UserExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, UserExecution] = {}

    async def get_by_id(self, id: UserExecutionId) -> UserExecution | None:
        return self._store.get(id.value)

    async def save(self, user_execution: UserExecution) -> None:
        self._store[user_execution.id.value] = user_execution

    async def delete(self, id: UserExecutionId) -> None:
        self._store.pop(id.value, None)

    async def exists(self, id: UserExecutionId) -> bool:
        return id.value in self._store
