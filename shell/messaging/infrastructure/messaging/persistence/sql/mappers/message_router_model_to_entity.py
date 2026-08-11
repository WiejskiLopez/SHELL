from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from shell.messaging.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_context import (
    MessageContext,
)
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_data import (
    MessageData,
)
from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)
from shell.platform.domain.value_objects.created_at import CreatedAt

if TYPE_CHECKING:
    from shell.messaging.infrastructure.messaging.persistence.sql.models.message_router import (
        MessageRouterModel,
    )


def message_router_model_to_entity(model: MessageRouterModel) -> MessageRouter:
    def _utc(dt: datetime) -> datetime:
        return dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt

    return MessageRouter.restore(
        id=MessageRouterId(model.id),
        message_data=MessageData(model.message_data),
        message_context=MessageContext(model.message_context),
        created_at=CreatedAt.from_datetime(_utc(model.created_at)),
    )
