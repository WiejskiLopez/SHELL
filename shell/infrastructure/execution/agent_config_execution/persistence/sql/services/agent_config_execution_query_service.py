from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.execution.agent_config_execution.dto.agent_config_execution import (
    AgentConfigExecutionDto,
)
from shell.infrastructure.execution.agent_config_execution.persistence.sql.models.agent_config_execution import (
    AgentConfigExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AgentConfigExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, agent_config_execution_id: str) -> AgentConfigExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(AgentConfigExecutionModel).where(
                AgentConfigExecutionModel.id == agent_config_execution_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return AgentConfigExecutionDto(
                id=model.id,
                agent_execution_id=model.agent_execution_id,
                config_data=model.config_data,
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
