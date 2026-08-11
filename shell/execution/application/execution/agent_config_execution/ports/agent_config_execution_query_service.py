from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.execution.application.execution.agent_config_execution.dto.agent_config_execution import (
        AgentConfigExecutionDto,
    )


class AgentConfigExecutionQueryService(Protocol):
    async def get_by_id(self, agent_config_execution_id: str) -> AgentConfigExecutionDto | None: ...
