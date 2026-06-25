from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_config_execution import (
        AgentConfigExecution,
    )
    from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
        AgentConfigExecutionId,
    )
    from shell.domain.execution.aggregates.session.value_objects.session_id import SessionId


class AgentConfigExecutionRepository(Protocol):
    async def get_by_id(
        self, agent_config_execution_id: AgentConfigExecutionId
    ) -> AgentConfigExecution | None: ...

    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> bool: ...
    
    async def get_by_session_id(
        self, session_id: SessionId
    ) -> AgentConfigExecution | None: ...

    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> bool: ...
    
    async def save(self, agent_config_execution: AgentConfigExecution) -> None: ...
    async def delete(self, id: object) -> None: ...
    async def exists(self, id: object) -> bool: ...
    