from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.application.execution.edge_link_execution.dto.edge_link_execution import (
    EdgeLinkExecutionDto,
)
from shell.execution_service.infrastructure.execution.edge_link_execution.persistence.sql.models.edge_link_execution import (
    EdgeLinkExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class EdgeLinkExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, edge_link_execution_id: str) -> EdgeLinkExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(EdgeLinkExecutionModel).where(
                EdgeLinkExecutionModel.id == edge_link_execution_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return EdgeLinkExecutionDto(
                id=model.id,
                node_execution_id=model.node_execution_id,
                edge_execution_id=model.edge_execution_id,
                created_at=model.created_at,
                updated_at=model.updated_at,
                deleted_at=model.deleted_at,
            )
