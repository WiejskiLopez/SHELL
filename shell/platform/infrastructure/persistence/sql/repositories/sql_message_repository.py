from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.messaging.aggregates.message_router.repositories.message_router_repository import (
    MessageRouterRepository,
)
from shell.platform.infrastructure.persistence.sql.mappers.message_mappers import (
    message_entity_to_model,
    message_model_to_entity,
)

from ..models.message.message import MessageModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
    from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId


class SqlMessageRouterRepository(MessageRouterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, message: MessageRouter) -> None:
        model = await self._session.get(MessageModel, message.id.value)
        if model is None:
            model = message_entity_to_model(message)
            self._session.add(model)
        else:
            model.message_data = message.message_data.value  # type: ignore[assignment]

    async def get_by_id(self, message_id: MessageId) -> MessageRouter | None:
        query = select(MessageModel).where(MessageModel.id == message_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return message_model_to_entity(row) if row else None
