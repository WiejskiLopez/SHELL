from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.platform.aggregates.message.repositories.message_repository import (
    MessageRepository,
)
from shell.infrastructure.platform.persistence.sql.mappers.message_mappers import (
    message_entity_to_model,
    message_model_to_entity,
)
from sqlalchemy import select

from ..models.message.message import MessageModel

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message
    from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
    from sqlalchemy.ext.asyncio import AsyncSession


class SqlMessageRepository(MessageRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def save(self, message: Message) -> None:
        model = await self._session.get(MessageModel, message.id.value)
        if model is None:
            model = message_entity_to_model(message)
            self._session.add(model)
        else:
            model.message_type = message.message_type.value
            model.business_payload = message.business_payload.to_dict()
            model.message_metadata = message.metadata.to_dict()
            model.source = message.source.value
            model.destination = message.destination.value
            model.status = message.status.value
            mat = message.materialized_metadata
            model.workflow_id = mat.workflow_id or None
            model.step = mat.step or None
            model.sequence_id = mat.sequence_id or None
            model.source_node_execution_id = mat.source_node_execution_id or None
            model.target_node_execution_id = mat.target_node_execution_id or None
            model.source_role = mat.source_role or None
            model.target_role = mat.target_role or None
            model.received_at = message.received_at.value if message.received_at else None

    async def get_by_id(self, message_id: MessageId) -> Message | None:
        query = select(MessageModel).where(MessageModel.id == message_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return message_model_to_entity(row) if row else None

    async def list_by_workflow_id(self, workflow_id: str) -> list[Message]:
        query = select(MessageModel).where(MessageModel.workflow_id == workflow_id)
        rows = (await self._session.execute(query)).scalars().all()
        return [message_model_to_entity(row) for row in rows if row]

    async def list_by_source(self, source: str) -> list[Message]:
        query = select(MessageModel).where(MessageModel.source == source)
        rows = (await self._session.execute(query)).scalars().all()
        return [message_model_to_entity(row) for row in rows if row]

    async def list_by_destination(self, destination: str) -> list[Message]:
        query = select(MessageModel).where(MessageModel.destination == destination)
        rows = (await self._session.execute(query)).scalars().all()
        return [message_model_to_entity(row) for row in rows if row]
