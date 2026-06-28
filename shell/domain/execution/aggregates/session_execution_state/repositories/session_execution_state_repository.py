from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
        SessionExecutionId,
    )
    from shell.domain.execution.aggregates.session_execution_state.session_execution_state import (
        SessionExecutionState,
    )
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from shell.domain.platform.value_objects.state_direction import StateDirection


class SessionExecutionStateRepository(Protocol):
    async def get_latest_by_session_execution_id(
        self, session_execution_id: SessionExecutionId, direction: StateDirection | None = None
    ) -> SessionExecutionState | None: ...

    async def save(self, payload: SessionExecutionState) -> None: ...
    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> ExistsResult: ...
