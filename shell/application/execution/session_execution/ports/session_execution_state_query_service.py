from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.session_execution.dto.session_execution_state import (
        SessionExecutionStateDto,
    )


class SessionExecutionStateQueryService(Protocol):
    async def get_by_id(
        self, session_execution_state_id: str
    ) -> SessionExecutionStateDto | None: ...
