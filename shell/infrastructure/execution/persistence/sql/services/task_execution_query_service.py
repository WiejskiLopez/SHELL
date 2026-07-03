from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.execution.dto.graph_node_execution import GraphNodeExecutionDto
from shell.application.execution.dto.task_execution import TaskExecutionDto
from shell.infrastructure.execution.persistence.sql.models import (
    GraphExecutionModel,
    GraphNodeExecutionModel,
    GraphNodeLinkExecutionModel,
    TaskExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class TaskExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_task_execution_by_name(self, name: str) -> TaskExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(TaskExecutionModel).where(TaskExecutionModel.name == name)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None

            graph_stmt = select(GraphExecutionModel).where(
                GraphExecutionModel.task_execution_id == model.id
            )
            graph_res = await session.execute(graph_stmt)
            graph_model = graph_res.scalar_one_or_none()

            graph_node_executions: list[GraphNodeExecutionDto] = []
            if graph_model is not None:
                node_stmt = (
                    select(GraphNodeExecutionModel)
                    .join(
                        GraphNodeLinkExecutionModel,
                        GraphNodeLinkExecutionModel.graph_node_execution_id
                        == GraphNodeExecutionModel.id,
                    )
                    .where(GraphNodeLinkExecutionModel.graph_execution_id == graph_model.id)
                )
                node_models = (await session.execute(node_stmt)).scalars().all()
                graph_node_executions = [
                    GraphNodeExecutionDto(
                        id=node_model.id,
                        position=node_model.position,
                        mode=node_model.mode,
                        role=node_model.role,
                        node_type=node_model.node_type,
                        model=node_model.model,
                        command=node_model.command,
                    )
                    for node_model in node_models
                ]

            return TaskExecutionDto(
                id=model.id,
                name=model.name,
                body=model.body or "",
                created_at=model.created_at,
                graph_node_executions=tuple(graph_node_executions),
            )

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        return await self.get_task_execution_by_name(name)
