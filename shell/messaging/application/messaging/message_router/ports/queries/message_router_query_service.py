from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.messaging.application.messaging.message_router.dto.message_router import (
        MessageRouterDto,
    )


class MessageRouterQueryService(Protocol):
    async def get_by_id(self, message_id: str) -> MessageRouterDto | None: ...
