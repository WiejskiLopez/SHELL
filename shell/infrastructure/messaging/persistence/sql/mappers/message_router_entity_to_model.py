from __future__ import annotations

from typing import TYPE_CHECKING

from shell.infrastructure.messaging.persistence.sql.models.message_router import MessageRouterModel

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter


def message_router_entity_to_model(message: MessageRouter) -> MessageRouterModel:
    return MessageRouterModel(
        id=message.id.value,
        message_data=message.message_data.value,
        created_at=message.created_at.value,
    )
