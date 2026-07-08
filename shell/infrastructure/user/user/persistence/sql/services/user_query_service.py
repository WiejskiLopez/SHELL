from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.user.user.dto.user import UserDto
from shell.infrastructure.user.user.persistence.sql.models.user import UserModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UserQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, user_id: str) -> UserDto | None:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(UserModel.id == user_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return UserDto(
                id=model.id,
                email=model.email,
                status=model.status,
                created_at=model.created_at,
                updated_at=model.updated_at,
                deleted_at=model.deleted_at,
            )
