from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.platform.dto.message import MessageDto
    from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId


class MessageQueryService(Protocol):
    async def get_by_id(self, message_id: MessageId) -> MessageDto | None: ...

    async def list_by_workflow_id(self, workflow_id: str) -> list[MessageDto]: ...

    async def list_by_source(self, source: str) -> list[MessageDto]: ...

    async def list_by_destination(self, destination: str) -> list[MessageDto]: ...
