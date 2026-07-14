from __future__ import annotations

from shell.domain.messaging.aggregates.message_router.message_router import MessageRouter
from shell.domain.messaging.aggregates.message_router.repositories.message_router_repository import (
    MessageRouterRepository,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_id import MessageId
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemoryMessageRouterRepository(InMemoryRepository[MessageRouter, MessageId], MessageRouterRepository):
    pass
