from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.session_execution.dto.session_execution import (
        SessionExecutionDto,
    )


class SessionExecutionQueryService(Protocol):
    async def get_by_id(self, session_execution_id: str) -> SessionExecutionDto | None: ...
