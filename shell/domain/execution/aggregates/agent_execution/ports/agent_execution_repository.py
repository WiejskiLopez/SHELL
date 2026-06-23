from __future__ import annotations

from typing import Protocol

from shell.domain.execution.aggregates.agent_execution.agent_execution import (
    AgentExecution,
)
from shell.domain.execution.aggregates.agent_execution.agent_execution_id import (
    AgentExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.graph_node_execution_id import (
    GraphNodeExecutionId,
)


class AgentExecutionRepository(Protocol):
    async def get_by_id(self, id_: AgentExecutionId) -> AgentExecution | None: ...

    async def get_by_node_execution_id(
        self, node_id: GraphNodeExecutionId
    ) -> AgentExecution | None: ...

    async def save(self, agent_execution: AgentExecution) -> None: ...
