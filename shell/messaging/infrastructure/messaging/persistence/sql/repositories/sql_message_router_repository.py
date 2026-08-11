from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import exists as sa_exists
from sqlalchemy import select

from shell.messaging.domain.messaging.aggregates.message_router.repositories.message_router_repository import (
    MessageRouterRepository,
)
from shell.messaging.infrastructure.messaging.persistence.sql.mappers.message_router_entity_to_model import (
    message_router_entity_to_model,
)
from shell.messaging.infrastructure.messaging.persistence.sql.mappers.message_router_model_to_entity import (
    message_router_model_to_entity,
)
from shell.platform.domain.value_objects.exists_result import ExistsResult

from ..models.message_router import MessageRouterModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.messaging.domain.messaging.aggregates.message_router.message_router import (
        MessageRouter,
    )
    from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
        MessageRouterId,
    )


class SqlMessageRouterRepository(MessageRouterRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, message: MessageRouter) -> None:
        model = await self._session.get(MessageRouterModel, message.id.value)
        if model is None:
            model = message_router_entity_to_model(message)
            self._session.add(model)
        else:
            model.message_data = message.message_data.value
            model.message_context = message.message_context.value

    async def get_by_id(self, message_id: MessageRouterId) -> MessageRouter | None:
        query = select(MessageRouterModel).where(MessageRouterModel.id == message_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return message_router_model_to_entity(row) if row else None

    async def delete(self, id: MessageRouterId) -> None:
        model = await self._session.get(MessageRouterModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: MessageRouterId) -> ExistsResult:
        stmt = select(sa_exists().where(MessageRouterModel.id == id.value))
        result = await self._session.execute(stmt)
        return ExistsResult(result.scalar() or False)
