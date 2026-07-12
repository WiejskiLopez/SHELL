from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.user_execution.value_objects.user_execution_id import (
        UserExecutionId,
    )
    from shell.domain.execution.aggregates.user_execution_state.user_execution_state import (
        UserExecutionState,
    )
    from shell.domain.execution.aggregates.user_execution_state.value_objects.user_execution_state_id import (
        UserExecutionStateId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.platform.domain.value_objects.state_direction import StateDirection


class UserExecutionStateRepository(Protocol):
    async def get_by_id(
        self, id: UserExecutionStateId
    ) -> UserExecutionState | None: ...

    async def get_latest_by_user_execution_id(
        self, user_execution_id: UserExecutionId, direction: StateDirection | None = None
    ) -> UserExecutionState | None: ...

    async def save(self, payload: UserExecutionState) -> None: ...
    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...
