from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shell.application.dto.dto import GraphNodeExecutionResultDto
from shell.infrastructure.persistence.sql.models import WorkflowModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class NodeResultQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_graph_node_execution_result(
        self, graph_node_execution_id: str, workflow_id: str
    ) -> GraphNodeExecutionResultDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(WorkflowModel)
                .options(selectinload(WorkflowModel.graph_node_execution_result_models))
                .where(WorkflowModel.id == workflow_id)
            )
            res = await session.execute(stmt)
            wf = res.scalar_one_or_none()
            if not wf:
                return None
            result_model = next(
                (
                    node_result_model
                    for node_result_model in wf.graph_node_execution_result_models
                    if node_result_model.graph_node_execution_id == graph_node_execution_id
                ),
                None,
            )
            if not result_model:
                return None
            return GraphNodeExecutionResultDto(
                id=result_model.id,
                graph_node_execution_id=result_model.graph_node_execution_id,
                workflow_id=result_model.workflow_id,
                status=result_model.status,
                stdout=result_model.stdout,
                stderr=result_model.stderr,
                artifact_uri=result_model.artifact_uri,
                created_at=result_model.created_at,
            )
