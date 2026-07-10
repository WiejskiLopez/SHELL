from __future__ import annotations

from datetime import UTC, datetime

from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.domain.messaging.aggregates.message_router.value_objects.message_data import MessageData
from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId
from shell.infrastructure.messaging.persistence.sql.models.message import MessageModel
from shell.platform.domain.value_objects.created_at import CreatedAt


def message_entity_to_model(message: MessageRouter) -> MessageModel:
    return MessageModel(
        id=message.id.value,
        message_data=message.message_data.value,
        created_at=message.created_at.value,
    )


def message_model_to_entity(model: MessageModel) -> MessageRouter:
    def _utc(dt: datetime | None) -> datetime | None:
        if dt is None:
            return None
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

    return MessageRouter.restore(
        id=MessageId(model.id),
        message_data=MessageData(dict(model.message_data)),
        created_at=CreatedAt.from_datetime(_utc(model.created_at)),
    )
