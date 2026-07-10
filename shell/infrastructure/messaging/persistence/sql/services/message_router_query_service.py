from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.messaging.message_router.dto.message_router import MessageRouterDto
from shell.infrastructure.messaging.persistence.sql.models.message import MessageModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class MessageRouterQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, message_id: str) -> MessageRouterDto | None:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.id == message_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return MessageRouterDto(
                id=model.id,
                message_data=model.message_data,
                created_at=model.created_at,
            )

    async def list_by_workflow_id(self, workflow_id: str) -> list[MessageRouterDto]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.workflow_id == workflow_id)
            res = await session.execute(stmt)
            return [
                MessageRouterDto(
                    id=model.id,
                    message_data=model.message_data,
                    created_at=model.created_at,
                )
                for model in res.scalars()
            ]

    async def list_by_source(self, source: str) -> list[MessageRouterDto]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.source == source)
            res = await session.execute(stmt)
            return [
                MessageRouterDto(
                    id=model.id,
                    message_data=model.message_data,
                    created_at=model.created_at,
                )
                for model in res.scalars()
            ]

    async def list_by_destination(self, destination: str) -> list[MessageRouterDto]:
        async with self._session_factory() as session:
            stmt = select(MessageModel).where(MessageModel.destination == destination)
            res = await session.execute(stmt)
            return [
                MessageRouterDto(
                    id=model.id,
                    message_data=model.message_data,
                    created_at=model.created_at,
                )
                for model in res.scalars()
            ]


__all__ = [
    "MessageRouterQueryService",
]
