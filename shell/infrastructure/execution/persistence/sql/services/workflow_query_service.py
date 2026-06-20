from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shell.application.platform.dto import GraphNodeExecutionStateDto, WorkflowDto
from shell.infrastructure.execution.persistence.sql.models import (
    WorkflowModel
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class WorkflowQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(WorkflowModel)
                .options(selectinload(WorkflowModel.graph_node_execution_state_models))
                .where(WorkflowModel.id == workflow_id)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return WorkflowDto(
                id=model.id,
                status=model.status,
                created_at=model.created_at,
                version=model.version,
                cursor=model.current_graph_node_execution_id,
                graph_node_execution_states={
                    state_model.graph_node_execution_id: GraphNodeExecutionStateDto(
                        graph_node_execution_id=state_model.graph_node_execution_id,
                        status=state_model.status,
                        step=state_model.step,
                        updated_at=state_model.updated_at,
                    )
                    for state_model in model.graph_node_execution_state_models
                },
            )
