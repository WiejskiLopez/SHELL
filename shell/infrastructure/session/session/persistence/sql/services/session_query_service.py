from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.sql import func

from shell.application.session.session.dto.session import SessionDto
from shell.infrastructure.session.session.persistence.sql.models.session import SessionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, session_id: str) -> SessionDto | None:
        async with self._session_factory() as session:
            stmt = select(SessionModel).where(SessionModel.id == session_id)
            res = await session.execute(stmt)
            session_model = res.scalar_one_or_none()
            if not session_model:
                return None
            return SessionDto(
                id=session_model.id,
                user_id=session_model.user_id,
                goal=session_model.goal,
                status=session_model.status,
                opened_at=session_model.opened_at,
                closed_at=session_model.closed_at,
                created_at=session_model.created_at,
                updated_at=session_model.updated_at,
                deleted_at=session_model.deleted_at,
            )

    async def list_all(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        user_id: str | None = None,
    ) -> tuple[list[SessionDto], int]:
        async with self._session_factory() as session:
            filters = [SessionModel.user_id == user_id] if user_id is not None else []
            count_stmt = select(func.count()).select_from(SessionModel).where(*filters)
            total = (await session.execute(count_stmt)).scalar_one()

            stmt = (
                select(SessionModel)
                .where(*filters)
                .order_by(SessionModel.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            rows = (await session.execute(stmt)).scalars().all()
            dtos = [
                SessionDto(
                    id=row.id,
                    user_id=row.user_id,
                    goal=row.goal,
                    status=row.status,
                    opened_at=row.opened_at,
                    closed_at=row.closed_at,
                    created_at=row.created_at,
                    updated_at=row.updated_at,
                    deleted_at=row.deleted_at,
                )
                for row in rows
            ]
            return dtos, total
