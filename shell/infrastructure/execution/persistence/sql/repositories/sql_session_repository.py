from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from shell.domain.execution.repositories.session_repository import SessionRepository
from shell.domain.platform.value_objects.ids import SessionId

from shell.infrastructure.platform.persistence.sql.mappers import (
    message_entity_to_model,
    message_model_to_entity,
    session_entity_to_model,
    session_model_to_entity,
)
from ..models import MessageModel, SessionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.execution.entities.session import Message, Session


class SqlSessionRepository(SessionRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, session: Session) -> None:
        model = session_entity_to_model(session)
        await self._session.merge(model)
        for message in session.messages:
            await self._session.merge(message_entity_to_model(message))

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        query = (
            select(SessionModel)
            .options(selectinload(SessionModel.messages))
            .where(SessionModel.id == session_id.value)
        )
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        return session_model_to_entity(row)

    async def get_messages(self, session_id: SessionId) -> list[Message]:
        query = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id.value)
            .order_by(MessageModel.created_at)
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [message_model_to_entity(row) for row in rows]
