from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.execution.agent_skill_execution.dto.agent_skill_execution import (
    AgentSkillExecutionDto,
)
from shell.infrastructure.execution.agent_skill_execution.persistence.sql.models.agent_skill_execution import (
    AgentSkillExecutionModel,
)
from shell.platform.types import JsonStr

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class AgentSkillExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(
        self, agent_skill_execution_id: str
    ) -> AgentSkillExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(AgentSkillExecutionModel).where(
                AgentSkillExecutionModel.id == agent_skill_execution_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return AgentSkillExecutionDto(
                id=model.id,
                agent_execution_id=model.agent_execution_id,
                skill_data=JsonStr(json.dumps(dict(model.skill_data))),
                created_at=model.created_at,
            )


