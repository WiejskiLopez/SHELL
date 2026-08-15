from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.sql import func

from shell.execution_service.application.execution.node_execution.dto.node_execution import (
    NodeExecutionDto,
)
from shell.execution_service.application.execution.task_execution.dto.task_execution import (
    TaskExecutionDto,
)
from shell.execution_service.infrastructure.execution.graph_execution.persistence.sql.models import (
    GraphExecutionModel,
)
from shell.execution_service.infrastructure.execution.node_execution.persistence.sql.models import (
    NodeExecutionModel,
)
from shell.execution_service.infrastructure.execution.node_link_execution.persistence.sql.models import (
    NodeLinkExecutionModel,
)
from shell.execution_service.infrastructure.execution.task_execution.persistence.sql.models import (
    TaskExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class TaskExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, task_execution_id: str) -> TaskExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(TaskExecutionModel).where(TaskExecutionModel.id == task_execution_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return TaskExecutionDto(
                id=model.id,
                name=model.name,
                created_at=model.created_at,
                work_dir=model.work_dir,
                workflow_id=model.workflow_id,
                updated_at=model.updated_at,
                deleted_at=model.deleted_at,
            )

    async def list_all(
        self, *, page: int = 1, page_size: int = 100
    ) -> tuple[list[TaskExecutionDto], int]:
        async with self._session_factory() as session:
            count_stmt = select(func.count()).select_from(TaskExecutionModel)
            total = (await session.execute(count_stmt)).scalar_one()

            offset = (page - 1) * page_size
            stmt = (
                select(TaskExecutionModel)
                .order_by(TaskExecutionModel.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            rows = (await session.execute(stmt)).scalars().all()

            dtos = [
                TaskExecutionDto(
                    id=r.id,
                    name=r.name,
                    created_at=r.created_at,
                    work_dir=r.work_dir,
                    workflow_id=r.workflow_id,
                    updated_at=r.updated_at,
                    deleted_at=r.deleted_at,
                )
                for r in rows
            ]
            return dtos, total

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

            node_executions: list[NodeExecutionDto] = []
            if graph_model is not None:
                node_stmt = (
                    select(NodeExecutionModel)
                    .join(
                        NodeLinkExecutionModel,
                        NodeLinkExecutionModel.node_execution_id == NodeExecutionModel.id,
                    )
                    .where(NodeLinkExecutionModel.graph_execution_id == graph_model.id)
                )
                node_models = (await session.execute(node_stmt)).scalars().all()
                node_executions = [
                    NodeExecutionDto(
                        id=node_model.id,
                        node_type=node_model.node_type,
                        model=node_model.model,
                        command=node_model.command,
                    )
                    for node_model in node_models
                ]

            return TaskExecutionDto(
                id=model.id,
                name=model.name,
                created_at=model.created_at,
                node_executions=tuple(node_executions),
            )

    async def get_current_task(self, name: str) -> TaskExecutionDto | None:
        return await self.get_task_execution_by_name(name)
