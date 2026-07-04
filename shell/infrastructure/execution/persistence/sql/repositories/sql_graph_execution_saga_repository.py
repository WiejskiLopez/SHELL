from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.infrastructure.execution.persistence.sql.models.saga_state import (
    GraphExecutionSagaStateModel,
)
from shell.process.execution.graph_execution_saga.state import (
    GraphExecutionSagaState,
    GraphExecutionSagaStatus,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphExecutionSagaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, saga: GraphExecutionSagaState) -> None:
        model = await self._session.get(GraphExecutionSagaStateModel, saga.saga_id)
        if model is None:
            model = GraphExecutionSagaStateModel(
                id=saga.saga_id,
                graph_execution_id=saga.graph_execution_id,
                expected_nodes_count=saga.expected_nodes_count,
                node_definition_executions=saga.node_definition_executions,
                status=saga.status.value,
            )
            self._session.add(model)
        else:
            model.expected_nodes_count = saga.expected_nodes_count
            model.node_definition_executions = saga.node_definition_executions
            model.status = saga.status.value

    async def get_by_graph_execution_id(
        self, graph_execution_id: str
    ) -> GraphExecutionSagaState | None:
        query = select(GraphExecutionSagaStateModel).where(
            GraphExecutionSagaStateModel.graph_execution_id == graph_execution_id
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        return GraphExecutionSagaState(
            saga_id=row.id,
            graph_execution_id=row.graph_execution_id,
            expected_nodes_count=row.expected_nodes_count,
            node_definition_executions=dict(row.node_definition_executions or {}),
            status=GraphExecutionSagaStatus(row.status),
            version=row.version,
        )
