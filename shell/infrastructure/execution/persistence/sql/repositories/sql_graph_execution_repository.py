from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.execution.aggregates.graph_execution.repositories.graph_execution_repository import (
    GraphExecutionRepository,
)
from shell.domain.execution.value_objects.ids import (  # noqa: TC002 — GraphExecutionId używany w konstruktorach w repozytorium
    GraphExecutionId,
    TaskExecutionId,
    WorkflowId,
)
from shell.infrastructure.platform.persistence.sql.mappers import (
    graph_execution_entity_to_model,
    graph_execution_model_to_entity,
)
from sqlalchemy import select

from ..models import GraphExecutionModel
from ..models.task_execution import TaskExecutionModel

if TYPE_CHECKING:
    from shell.domain.execution.aggregates.graph_execution import GraphExecution
    from sqlalchemy import Select
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlGraphExecutionRepository(GraphExecutionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _base_query(self) -> Select[tuple[GraphExecutionModel]]:
        return select(GraphExecutionModel)

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

    async def get_by_parent_id(
        self, parent_graph_execution_id: GraphExecutionId
    ) -> list[GraphExecution]:
        query = self._base_query().where(
            GraphExecutionModel.parent_graph_execution_id == parent_graph_execution_id.value
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [graph_execution_model_to_entity(row) for row in rows if row is not None]

    async def get_by_workflow_id(self, workflow_id: WorkflowId) -> list[GraphExecution]:
        query = (
            self._base_query()
            .join(
                TaskExecutionModel,
                GraphExecutionModel.task_execution_id == TaskExecutionModel.id,
            )
            .where(TaskExecutionModel.workflow_id == workflow_id.value)
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [graph_execution_model_to_entity(row) for row in rows if row is not None]

    async def save(self, graph_execution: GraphExecution) -> None:
        graph_execution_model = await self._session.get(GraphExecutionModel, graph_execution.id.value)
        if graph_execution_model is None:
            graph_execution_model = graph_execution_entity_to_model(graph_execution)
            self._session.add(graph_execution_model)
        else:
            graph_execution_model.task_execution_id = graph_execution.task_execution_id.value
            graph_execution_model.parent_graph_execution_id = (
                graph_execution.parent_graph_execution_id.value
                if graph_execution.parent_graph_execution_id
                else None
            )
            graph_execution_model.depth = graph_execution.depth.value if graph_execution.depth else 0
            graph_execution_model.initialization_status = graph_execution.initialization_status.value
            graph_execution_model.graph_node_definition_executions = {
                slot.graph_node_definition_id.value: slot.graph_node_execution_id.value if slot.graph_node_execution_id else None
                for slot in graph_execution.graph_node_definition_execution_slots
            }


__all__ = [
    "GraphExecutionModel",
    "SqlGraphExecutionRepository",
    "TaskExecutionModel",
]
