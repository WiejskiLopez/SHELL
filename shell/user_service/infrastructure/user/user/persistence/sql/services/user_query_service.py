from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.sql import func

from shell.user_service.application.user.user.dto.user import UserDto
from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel

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
                changed_at=model.changed_at,
                deleted_at=model.deleted_at,
            )

    async def get_by_email(self, email: str) -> UserDto | None:
        async with self._session_factory() as session:
            stmt = select(UserModel).where(UserModel.email == email)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return UserDto(
                id=model.id,
                email=model.email,
                status=model.status,
                created_at=model.created_at,
                changed_at=model.changed_at,
                deleted_at=model.deleted_at,
            )

    async def list_all(self, *, page: int = 1, page_size: int = 100) -> tuple[list[UserDto], int]:
        async with self._session_factory() as session:
            count_stmt = select(func.count()).select_from(UserModel)
            total = (await session.execute(count_stmt)).scalar_one()

            offset = (page - 1) * page_size
            stmt = (
                select(UserModel)
                .order_by(UserModel.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            rows = (await session.execute(stmt)).scalars().all()

            dtos = [
                UserDto(
                    id=r.id,
                    email=r.email,
                    status=r.status,
                    created_at=r.created_at,
                    changed_at=r.changed_at,
                    deleted_at=r.deleted_at,
                )
                for r in rows
            ]
            return dtos, total
