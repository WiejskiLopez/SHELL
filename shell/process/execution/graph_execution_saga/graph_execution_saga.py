from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaState,
    GraphExecutionSagaStatus,
)

if TYPE_CHECKING:
    from shell.process.execution.graph_execution_saga.ports.graph_execution_saga_repository import (
        GraphExecutionSagaRepository,
    )


class GraphExecutionSaga:
    def __init__(self, repository: GraphExecutionSagaRepository) -> None:
        self._repository = repository

    async def create_saga(
        self, graph_execution_id: str, expected_nodes_count: int
    ) -> GraphExecutionSagaState:
        saga = GraphExecutionSagaState(
            saga_id=str(uuid.uuid4()),
            graph_execution_id=graph_execution_id,
            expected_nodes_count=expected_nodes_count,
        )
        await self._repository.save(saga)
        return saga

    async def record_node_execution(
        self,
        graph_execution_id: str,
        node_definition_id: str,
        node_execution_id: str,
    ) -> GraphExecutionSagaState | None:
        saga = await self._repository.get_by_graph_execution_id(graph_execution_id)
        if saga is None or saga.status != GraphExecutionSagaStatus.PENDING:
            return saga
        saga.record_node_execution_created(node_definition_id, node_execution_id)
        await self._repository.save(saga)
        return saga
