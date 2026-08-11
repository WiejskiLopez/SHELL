from __future__ import annotations

from typing import TYPE_CHECKING

from shell.messaging.infrastructure.messaging.persistence.sql.models.message_router import (
    MessageRouterModel,
)

if TYPE_CHECKING:
    from shell.messaging.domain.messaging.aggregates.message_router.message_router import (
        MessageRouter,
    )


def message_router_entity_to_model(message: MessageRouter) -> MessageRouterModel:
    return MessageRouterModel(
        id=message.id.value,
        message_data=message.message_data.value,
        message_context=message.message_context.value,
        created_at=message.created_at.value if message.created_at else None,
        updated_at=message.updated_at.value,
        deleted_at=message._deleted_at.value if message._deleted_at is not None else None,
    )
