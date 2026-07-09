from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.messaging.dto.message_router import MessageRouterDto
    from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId


class MessageRouterQueryService(Protocol):
    async def get_by_id(self, message_id: MessageId) -> MessageRouterDto | None: ...

    async def list_by_workflow_id(self, workflow_id: str) -> list[MessageRouterDto]: ...

    async def list_by_source(self, source: str) -> list[MessageRouterDto]: ...

    async def list_by_destination(self, destination: str) -> list[MessageRouterDto]: ...
