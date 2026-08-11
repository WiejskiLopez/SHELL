from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.types import JsonStr
from shell.user.application.user.user_skill.dto.user_skill import UserSkillDto
from shell.user.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
    UserSkillModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UserSkillQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, user_skill_id: str) -> UserSkillDto | None:
        async with self._session_factory() as session:
            stmt = select(UserSkillModel).where(UserSkillModel.id == user_skill_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return UserSkillDto(
                id=model.id,
                user_id=model.user_id,
                skill_data=JsonStr(json.dumps(dict(model.skill_data))),
                created_at=model.created_at,
                updated_at=model.updated_at,
            )
