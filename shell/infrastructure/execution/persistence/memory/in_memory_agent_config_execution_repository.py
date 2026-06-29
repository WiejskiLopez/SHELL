from __future__ import annotations

from shell.domain.execution.aggregates.agent_config_execution.repositories.agent_config_execution_repository import (
    AgentConfigExecutionRepository,
)
from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
    AgentConfigExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)
from shell.domain.execution.aggregates.session_execution.value_objects.session_execution_id import (
    SessionExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)
from shell.domain.execution.aggregates.agent_config_execution import (
    AgentConfigExecution,
)
from shell.infrastructure.platform.persistence.in_memory_repository import (
    InMemoryRepository,
)


class InMemoryAgentConfigExecutionRepository(InMemoryRepository[AgentConfigExecution, AgentConfigExecutionId], AgentConfigExecutionRepository):  # type: ignore[misc]

    async def get_by_session_execution_id(
        self, session_execution_id: SessionExecutionId
    ) -> AgentConfigExecution | None:
        for item in self._store.values():
            if item.session_execution_id == session_execution_id:
                return item
        return None
