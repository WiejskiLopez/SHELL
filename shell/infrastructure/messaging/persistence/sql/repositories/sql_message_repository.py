from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.messaging.aggregates.message.repositories.message_repository import (
    MessageRepository,
)
from shell.infrastructure.messaging.persistence.sql.mappers.message_mappers import (
    message_entity_to_model,
    message_model_to_entity,
)

from ..models.message import MessageModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.messaging.aggregates.message.message import Message
    from shell.domain.messaging.aggregates.message.value_objects.destination import Destination
    from shell.domain.messaging.aggregates.message.value_objects.message_id import MessageId
    from shell.domain.messaging.aggregates.message.value_objects.source import Source
    from shell.domain.platform.value_objects.workflow_reference import WorkflowReference


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

    async def list_by_workflow_id(self, workflow_id: WorkflowReference) -> list[Message]:
        query = select(MessageModel).where(MessageModel.workflow_id == workflow_id.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [message_model_to_entity(row) for row in rows if row]

    async def list_by_source(self, source: Source) -> list[Message]:
        query = select(MessageModel).where(MessageModel.source == source.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [message_model_to_entity(row) for row in rows if row]

    async def list_by_destination(self, destination: Destination) -> list[Message]:
        query = select(MessageModel).where(MessageModel.destination == destination.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [message_model_to_entity(row) for row in rows if row]
