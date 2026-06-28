from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.user_execution import UserExecution
    from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.domain.execution.value_objects.exists_result import ExistsResult


class UserExecutionRepository(Protocol):
    async def get_by_id(self, id: UserExecutionId) -> UserExecution | None: ...
    async def save(self, user_execution: UserExecution) -> None: ...
    async def delete(self, id: UserExecutionId) -> None: ...
    async def exists(self, id: UserExecutionId) -> ExistsResult: ...
