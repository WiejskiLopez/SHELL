from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.execution.application.execution.user_execution.dto.user_execution import UserExecutionDto
from shell.execution.infrastructure.execution.user_execution.persistence.sql.models.user_execution import (
    UserExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UserExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, user_execution_id: str) -> UserExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(UserExecutionModel).where(UserExecutionModel.id == user_execution_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return UserExecutionDto(
                id=model.id,
                user_id=model.user_id,
                created_at=model.created_at,
            )
