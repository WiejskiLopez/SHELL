from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.messaging.aggregates.message.message import Message
from shell.domain.messaging.aggregates.message.repositories.message_repository import (
    MessageRepository,
)
from shell.domain.messaging.aggregates.message.value_objects.message_id import MessageId
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.messaging.aggregates.message.value_objects.destination import Destination
    from shell.domain.messaging.aggregates.message.value_objects.source import Source


class InMemoryMessageRepository(InMemoryRepository[Message, MessageId], MessageRepository):
    async def list_by_workflow_id(self, workflow_id: str) -> list[Message]:  # type: ignore[override]
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.materialized_metadata.workflow_id == workflow_id
        ]

    async def list_by_source(self, source: Source) -> list[Message]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.source.value == source.value
        ]

    async def list_by_destination(self, destination: Destination) -> list[Message]:
        return [
            copy.deepcopy(item)
            for item in self._store.values()
            if item.destination.value == destination.value
        ]
