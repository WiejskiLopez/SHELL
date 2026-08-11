from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.domain.execution.aggregates.session_execution.session_execution import (
        SessionExecution,
    )
    from shell.execution.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.execution.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class SessionExecutionRepository(Protocol):
    async def get_by_id(self, id: SessionExecutionId) -> SessionExecution | None: ...
    async def get_by_user_execution_id(
        self, user_execution_id: UserExecutionId
    ) -> list[SessionExecution]: ...
    async def save(self, session_execution: SessionExecution) -> None: ...
    async def delete(self, id: SessionExecutionId) -> None: ...
    async def exists(self, id: SessionExecutionId) -> ExistsResult: ...
