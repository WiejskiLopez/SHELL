from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.platform.aggregates.message.repositories.message_repository import MessageRepository

if TYPE_CHECKING:
    from shell.domain.platform.aggregates.message.value_objects.message_id import MessageId
    from shell.domain.platform.aggregates.message.message import Message


class InMemoryMessageRepository(MessageRepository):
    def __init__(self) -> None:
        self._store: dict[str, Message] = {}

    async def save(self, message: Message) -> None:
        self._store[message.id.value] = copy.deepcopy(message)

    async def get_by_id(self, message_id: MessageId) -> Message | None:
        item = self._store.get(message_id.value)
        return copy.deepcopy(item) if item is not None else None

    async def list_by_workflow_id(self, workflow_id: str) -> list[Message]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.materialized_metadata.workflow_id == workflow_id
        ]

    async def list_by_source(self, source: str) -> list[Message]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.source.value == source
        ]

    async def list_by_destination(self, destination: str) -> list[Message]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.destination.value == destination
        ]
