from __future__ import annotations

import json
from datetime import UTC, datetime

from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.domain.messaging.aggregates.message_router.value_objects.message_data import MessageData
from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId
from shell.platform.domain.value_objects.created_at import CreatedAt
from shell.platform.infrastructure.persistence.sql.models.message.message import MessageModel
from shell.platform.types import JsonStr  # noqa: TC001 -- potrzebny w runtime


def message_entity_to_model(message: MessageRouter) -> MessageModel:
    return MessageModel(
        id=message.id.value,
        message_data=message.message_data.value,
        created_at=message.created_at.value,
    )

