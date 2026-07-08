from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.execution.agent_execution.dto.agent_execution import (
        AgentExecutionDto,
    )


class AgentExecutionQueryService(Protocol):
    async def get_by_id(self, agent_execution_id: str) -> AgentExecutionDto | None: ...
