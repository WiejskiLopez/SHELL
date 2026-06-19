from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.entities.session import Message, Session
from shell.domain.value_objects.ids import CorrelationId, MessageId, SessionId

from ..models import MessageModel, SessionModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlSessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, session: Session) -> None:
        model = SessionModel(
            id=session.id.value,
            goal=session.goal,
            status=session.status,
            opened_at=session.opened_at,
            closed_at=session.closed_at,
        )
        await self._session.merge(model)
        for message in session.messages:
            await self._session.merge(
                MessageModel(
                    id=message.id.value,
                    session_id=message.session_id.value,
                    correlation_id=message.correlation_id.value,
                    sender=message.sender,
                    receiver=message.receiver,
                    payload=message.payload,
                    created_at=message.created_at,
                )
            )

    async def get_by_id(self, session_id: SessionId) -> Session | None:
        query = select(SessionModel).where(SessionModel.id == session_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        if row is None:
            return None
        return Session(
            id=SessionId(row.id),
            goal=row.goal,
            status=row.status,
            opened_at=row.opened_at,
            closed_at=row.closed_at,
        )

    async def get_messages(self, session_id: SessionId) -> list[Message]:
        query = (
            select(MessageModel)
            .where(MessageModel.session_id == session_id.value)
            .order_by(MessageModel.created_at)
        )
        rows = (await self._session.execute(query)).scalars().all()
        return [
            Message(
                id=MessageId(message_model.id),
                session_id=SessionId(message_model.session_id),
                correlation_id=CorrelationId(message_model.correlation_id),
                sender=message_model.sender,
                receiver=message_model.receiver,
                payload=message_model.payload,
                created_at=message_model.created_at,
            )
            for message_model in rows
        ]
