from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution_service.application.execution.user_execution.dto.user_execution import (
        UserExecutionDto,
    )


class UserExecutionQueryService(Protocol):
    async def get_by_id(self, user_execution_id: str) -> UserExecutionDto | None: ...
