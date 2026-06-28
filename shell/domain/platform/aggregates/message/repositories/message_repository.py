from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.message import Message
    from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId


class MessageRepository(Protocol):
    async def save(self, message: Message) -> None: ...

    async def get_by_id(self, message_id: MessageId) -> Message | None: ...

    async def list_by_workflow_id(self, workflow_id: str) -> list[Message]: ...

    async def list_by_source(self, source: str) -> list[Message]: ...

    async def list_by_destination(self, destination: str) -> list[Message]: ...
