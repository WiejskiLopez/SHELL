from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.types import JsonStr
from shell.user_service.application.user.user_state.dto.user_state import UserStateDto
from shell.user_service.infrastructure.user.user_state.persistence.sql.models.user_state import (
    UserStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UserStateQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, user_state_id: str) -> UserStateDto | None:
        async with self._session_factory() as session:
            stmt = select(UserStateModel).where(UserStateModel.id == user_state_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return UserStateDto(
                id=model.id,
                user_id=model.user_id,
                direction=model.direction,
                state_data=JsonStr(json.dumps(dict(model.state_data))),
                created_at=model.created_at,
            )
