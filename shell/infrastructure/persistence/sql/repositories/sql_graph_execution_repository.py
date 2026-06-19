from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shell.domain.value_objects.ids import GraphExecutionId, TaskExecutionId

from ..mappers import (
    graph_execution_entity_to_model,
    graph_execution_model_to_entity,
)
from ..models import GraphExecutionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.aggregates.graph_execution import GraphExecution


class SqlGraphExecutionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None:
        query = (
            select(GraphExecutionModel)
            .options(selectinload(GraphExecutionModel.graph_node_execution_models))
            .where(GraphExecutionModel.id == graph_execution_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_model_to_entity(row) if row else None

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> GraphExecution | None:
        query = (
            select(GraphExecutionModel)
            .options(selectinload(GraphExecutionModel.graph_node_execution_models))
            .where(GraphExecutionModel.task_execution_id == task_execution_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_model_to_entity(row) if row else None

    async def save(self, graph_execution: GraphExecution) -> None:
        graph_execution_model = graph_execution_entity_to_model(graph_execution)
        await self._session.merge(graph_execution_model)
