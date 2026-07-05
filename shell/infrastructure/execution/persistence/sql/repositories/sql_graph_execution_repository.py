from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.infrastructure.execution.persistence.sql.mappers import (
    graph_execution_entity_to_model,
    graph_execution_model_to_entity,
    graph_execution_update_model,
)

from ..models import GraphExecutionModel

if TYPE_CHECKING:
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from shell.domain.execution.value_objects.ids import (
        GraphExecutionId,
        TaskExecutionId,
    )


class SqlGraphExecutionRepository(GraphExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[GraphExecutionModel]]:
        return select(GraphExecutionModel)

    def _active_query(self) -> Select[tuple[GraphExecutionModel]]:
        return self._base_query().where(GraphExecutionModel.deleted_at.is_(None))

    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None:
        query = self._base_query().where(GraphExecutionModel.id == graph_execution_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_model_to_entity(row) if row else None

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> list[GraphExecution]:
        query = self._active_query().where(
            GraphExecutionModel.task_execution_id == task_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [graph_execution_model_to_entity(row) for row in rows if row is not None]

    async def get_by_parent_id(
        self, parent_graph_execution_id: GraphExecutionId
    ) -> list[GraphExecution]:
        query = self._active_query().where(
            GraphExecutionModel.parent_graph_execution_id == parent_graph_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [graph_execution_model_to_entity(row) for row in rows if row is not None]

    async def save(self, graph_execution: GraphExecution) -> None:
        graph_execution_model = await self._session.get(
            GraphExecutionModel, graph_execution.id.value
        )
        if graph_execution_model is None:
            graph_execution_model = graph_execution_entity_to_model(graph_execution)
            self._session.add(graph_execution_model)
        else:
            graph_execution_update_model(graph_execution_model, graph_execution)

    async def delete(self, id: GraphExecutionId) -> None:
        model = await self._session.get(GraphExecutionModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: GraphExecutionId) -> ExistsResult:
        entity = await self.get_by_id(id)
        return ExistsResult(entity is not None)
