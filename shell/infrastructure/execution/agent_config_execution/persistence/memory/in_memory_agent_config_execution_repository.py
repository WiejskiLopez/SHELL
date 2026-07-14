from __future__ import annotations

from shell.domain.execution.aggregates.agent_config_execution import (
    AgentConfigExecution,
)
from shell.domain.execution.aggregates.agent_config_execution.repositories.agent_config_execution_repository import (
    AgentConfigExecutionRepository,
)
from shell.domain.execution.aggregates.agent_config_execution.value_objects.agent_config_execution_id import (
    AgentConfigExecutionId,  # noqa: TC002 -- TYPE_CHECKING import
)
from shell.platform.infrastructure.persistence.in_memory_repository import (
    InMemoryRepository,
)


class InMemoryAgentConfigExecutionRepository(  # type: ignore[misc]
    InMemoryRepository[AgentConfigExecution, AgentConfigExecutionId], AgentConfigExecutionRepository
):
    pass
