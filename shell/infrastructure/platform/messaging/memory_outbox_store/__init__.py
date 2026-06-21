"""InMemoryOutboxStore — in-process store for unit-testing the outbox pattern."""

from __future__ import annotations

from shell.infrastructure.platform.messaging.memory_outbox_store.in_memory_outbox_store import (
    InMemoryOutboxStore,
)
from shell.infrastructure.platform.messaging.memory_outbox_store.outbox_record import OutboxRecord

__all__ = [
    "OutboxRecord",
    "InMemoryOutboxStore",
]
