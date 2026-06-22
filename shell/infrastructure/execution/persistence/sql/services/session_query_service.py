from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.dto import SessionDto
from shell.infrastructure.execution.persistence.sql.models import SessionModel
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        async with self._session_factory() as session:
            stmt = select(SessionModel).where(SessionModel.id == session_id)
            res = await session.execute(stmt)
            session_model = res.scalar_one_or_none()
            if not session_model:
                return None
            return SessionDto(
                id=session_model.id,
                goal=session_model.goal,
                status=session_model.status,
                opened_at=session_model.opened_at,
                closed_at=session_model.closed_at,
            )
