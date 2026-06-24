from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.agent_config_execution.repositories.agent_config_execution_repository import (
    AgentConfigExecutionRepository,
)
from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
    AgentConfigExecutionId,  # noqa: TC002
)
from shell.domain.execution.aggregates.session.value_objects.session_id import (
    SessionId,  # noqa: TC002
)

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.agent_config_execution import (
        AgentConfigExecution,
    )


class InMemoryAgentConfigExecutionRepository(AgentConfigExecutionRepository):
    def __init__(self) -> None:
        self._store: dict[str, AgentConfigExecution] = {}

    async def get_by_id(
        self, agent_config_execution_id: AgentConfigExecutionId
    ) -> AgentConfigExecution | None:
        item = self._store.get(agent_config_execution_id.value)
        return copy.deepcopy(item) if item is not None else None

    async def get_by_session_id(
        self, session_id: SessionId
    ) -> AgentConfigExecution | None:
        for item in self._store.values():
            if item.session_id == session_id:
                return copy.deepcopy(item)
        return None

    async def save(self, agent_config_execution: AgentConfigExecution) -> None:
        self._store[agent_config_execution.id.value] = copy.deepcopy(agent_config_execution)
