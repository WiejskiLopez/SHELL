from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.execution.node_execution.dto.node_execution_result import (
    NodeExecutionResultDto,
)
from shell.infrastructure.execution.node_execution_state.persistence.sql.models.node_execution_state_aggregate import (
    NodeExecutionStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class NodeResultQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, node_execution_id: str) -> NodeExecutionResultDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(NodeExecutionStateModel)
                .where(NodeExecutionStateModel.node_execution_id == node_execution_id)
                .where(NodeExecutionStateModel.direction == "OUT")
                .limit(1)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            payload = model.state_data
            return NodeExecutionResultDto(
                id=model.id,
                node_execution_id=model.node_execution_id,
                workflow_id=payload.get("workflow_id", ""),
                status=payload.get("status", ""),
                stdout=payload.get("stdout", ""),
                stderr=payload.get("stderr", ""),
                artifact_uri=payload.get("artifact_uri", ""),
                created_at=model.created_at,
            )

    async def get_node_execution_result(
        self, node_execution_id: str, workflow_id: str
    ) -> NodeExecutionResultDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(NodeExecutionStateModel)
                .where(NodeExecutionStateModel.node_execution_id == node_execution_id)
                .where(NodeExecutionStateModel.direction == "OUT")
                .limit(1)
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            payload = model.state_data
            return NodeExecutionResultDto(
                id=model.id,
                node_execution_id=model.node_execution_id,
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
