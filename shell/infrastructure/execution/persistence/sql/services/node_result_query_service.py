from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.execution.dto.graph_node_execution_result import GraphNodeExecutionResultDto
from shell.infrastructure.execution.persistence.sql.models.graph_node_execution_state_aggregate import (
    GraphNodeExecutionStateModel,
)

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
                select(GraphNodeExecutionStateModel)
                .where(
                    GraphNodeExecutionStateModel.graph_node_execution_id == graph_node_execution_id
                )
                .where(GraphNodeExecutionStateModel.direction == "OUT")
                .where(GraphNodeExecutionStateModel.is_current == True)  # noqa: E712 -- comparison to True is intentional
                .limit(1)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            payload = model.state_data or {}
            return GraphNodeExecutionResultDto(
                id=model.id,
                graph_node_execution_id=model.graph_node_execution_id,
                workflow_id=workflow_id,
                status=payload.get("status", ""),
                stdout=payload.get("stdout", ""),
                stderr=payload.get("stderr", ""),
                artifact_uri=payload.get("artifact_uri", ""),
                created_at=model.created_at,
            )


__all__ = [
    "NodeResultQueryService",
]
