from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.messaging.domain.messaging.aggregates.message_router.message_router import (
        MessageRouter,
    )
    from shell.messaging.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
        MessageRouterId,
    )
    from shell.platform.domain.value_objects.exists_result import ExistsResult


class MessageRouterRepository(Protocol):
    async def save(self, message: MessageRouter) -> None: ...

    async def get_by_id(self, message_id: MessageRouterId) -> MessageRouter | None: ...

    async def delete(self, id: MessageRouterId) -> None: ...

    async def exists(self, id: MessageRouterId) -> ExistsResult: ...
