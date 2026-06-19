from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shell.application.dto import MessageDto, SessionDto
from shell.infrastructure.persistence.sql.models import SessionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class SessionQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_session_history(self, session_id: str) -> SessionDto | None:
        async with self._session_factory() as session:
            stmt = (
                select(SessionModel)
                .options(selectinload(SessionModel.messages))
                .where(SessionModel.id == session_id)
            )
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
                messages=[
                    MessageDto(
                        id=message.id,
                        session_id=message.session_id,
                        correlation_id=message.correlation_id,
                        sender=message.sender,
                        receiver=message.receiver,
                        payload=message.payload,
                        created_at=message.created_at,
                    )
                    for message in session_model.messages
                ],
            )
