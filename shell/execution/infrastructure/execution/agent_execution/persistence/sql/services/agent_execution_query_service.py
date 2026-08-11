from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution.application.execution.agent_execution.dto.agent_execution import (
    AgentExecutionDto,
)
from shell.execution.infrastructure.execution.agent_execution.persistence.sql.models.agent_execution import (
    AgentExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AgentExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, agent_execution_id: str) -> AgentExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(AgentExecutionModel).where(AgentExecutionModel.id == agent_execution_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return AgentExecutionDto(
                id=model.id,
                node_execution_id=model.node_execution_id,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
