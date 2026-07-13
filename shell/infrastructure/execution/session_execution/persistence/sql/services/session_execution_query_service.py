from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.execution.session_execution.dto.session_execution import (
    SessionExecutionDto,
)
from shell.infrastructure.execution.session_execution.persistence.sql.models.session_execution import (
    SessionExecutionModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionExecutionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, session_execution_id: str) -> SessionExecutionDto | None:
        async with self._session_factory() as session:
            stmt = select(SessionExecutionModel).where(
                SessionExecutionModel.id == session_execution_id
            )
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return SessionExecutionDto(
                id=model.id,
                user_execution_id=model.user_execution_id,
                session_id=model.session_id,
                created_at=model.created_at,
            )
