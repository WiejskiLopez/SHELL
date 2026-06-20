from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shell.domain.execution.repositories.graph_execution_repository import GraphExecutionRepository
from shell.domain.execution.value_objects.ids import GraphExecutionId, TaskExecutionId, WorkflowId

from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_execution_entity_to_model,
    graph_execution_model_to_entity,
)
from ..models import GraphExecutionModel
from ..models.task_execution import TaskExecutionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.aggregates.graph_execution import GraphExecution


class SqlGraphExecutionRepository(GraphExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self):
        return select(GraphExecutionModel).options(
            selectinload(GraphExecutionModel.graph_node_execution_models),
            selectinload(GraphExecutionModel.graph_node_transition_execution_models),
        )

    async def get_by_id(self, graph_execution_id: GraphExecutionId) -> GraphExecution | None:
        query = self._base_query().where(GraphExecutionModel.id == graph_execution_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_model_to_entity(row) if row else None

    async def get_by_task_execution_id(
        self, task_execution_id: TaskExecutionId
    ) -> GraphExecution | None:
        query = self._base_query().where(
            GraphExecutionModel.task_execution_id == task_execution_id.value
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        return graph_execution_model_to_entity(row) if row else None

    async def get_by_workflow_id(
        self, workflow_id: WorkflowId
    ) -> list[GraphExecution]:
        query = self._base_query().join(
            TaskExecutionModel,
            GraphExecutionModel.task_execution_id == TaskExecutionModel.id,
        ).where(
            TaskExecutionModel.workflow_id == workflow_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [graph_execution_model_to_entity(row) for row in rows if row is not None]

    async def save(self, graph_execution: GraphExecution) -> None:
        graph_execution_model = graph_execution_entity_to_model(graph_execution)
        await self._session.merge(graph_execution_model)
