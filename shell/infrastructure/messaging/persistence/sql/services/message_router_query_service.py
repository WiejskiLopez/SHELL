from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.messaging.message_router.dto.message_router import MessageRouterDto
from shell.infrastructure.messaging.persistence.sql.models.message_router import MessageRouterModel
from shell.platform.types import JsonStr

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
                message_data=JsonStr(json.dumps(dict(model.message_data))),
                created_at=model.created_at,
            )


__all__ = [
    "MessageRouterQueryService",
]


