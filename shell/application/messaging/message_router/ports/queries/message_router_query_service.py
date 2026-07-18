from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.messaging.message_router.dto.message_router import MessageRouterDto
    from shell.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
        MessageRouterId,
    )


class MessageRouterQueryService(Protocol):
    async def get_by_id(self, message_id: MessageRouterId) -> MessageRouterDto | None: ...
