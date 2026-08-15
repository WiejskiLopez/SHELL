from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution_service.application.execution.edge_execution.dto.edge_execution import (
    EdgeExecutionDto,
)
from shell.execution_service.infrastructure.execution.edge_execution.persistence.sql.models.edge_execution import (
    EdgeExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class EdgeExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, edge_execution_id: str) -> EdgeExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(EdgeExecutionModel).where(EdgeExecutionModel.id == edge_execution_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return EdgeExecutionDto(
                id=model.id,
                edge_definition_id=model.edge_definition_id,
                source_node_execution_id=model.source_node_execution_id,
                target_node_execution_id=model.target_node_execution_id,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
