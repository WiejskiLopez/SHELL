from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.messaging.application.messaging.message_router.dto.message_router import MessageRouterDto
from shell.messaging.infrastructure.messaging.persistence.sql.models.message_router import (
    MessageRouterModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class MessageRouterQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, message_id: str) -> MessageRouterDto | None:
        async with self._session_factory() as session:
            stmt = select(MessageRouterModel).where(MessageRouterModel.id == message_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return MessageRouterDto(
                id=model.id,
                message_data=model.message_data,
                message_context=model.message_context,
                created_at=model.created_at,
                updated_at=model.updated_at,
                deleted_at=model.deleted_at,
            )


__all__ = [
    "MessageRouterQueryService",
]
