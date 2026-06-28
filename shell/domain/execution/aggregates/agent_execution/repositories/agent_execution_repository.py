from __future__ import annotations

from typing import Protocol

from shell.domain.execution.aggregates.agent_execution.agent_execution import (
    AgentExecution,
)
from shell.domain.execution.aggregates.agent_execution.value_objects.agent_execution_id import (
    AgentExecutionId,
)
from shell.domain.execution.aggregates.graph_node_execution.value_objects.graph_node_execution_id import (
    GraphNodeExecutionId,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult


class AgentExecutionRepository(Protocol):
    async def get_by_id(self, id_: AgentExecutionId) -> AgentExecution | None: ...

    async def delete(self, id: AgentExecutionId) -> None: ...
    async def exists(self, id: AgentExecutionId) -> ExistsResult: ...
    
    async def get_by_node_execution_id(
        self, node_id: GraphNodeExecutionId
    ) -> AgentExecution | None: ...

    async def delete(self, id: AgentExecutionId) -> None: ...
    async def exists(self, id: AgentExecutionId) -> ExistsResult: ...
    
    async def save(self, agent_execution: AgentExecution) -> None: ...
    async def delete(self, id: AgentExecutionId) -> None: ...
    async def exists(self, id: AgentExecutionId) -> ExistsResult: ...
    