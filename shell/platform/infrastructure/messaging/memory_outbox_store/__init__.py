"""InMemoryOutboxStore — in-process store for unit-testing the outbox pattern."""

from __future__ import annotations

from shell.platform.infrastructure.messaging.memory_outbox_store.in_memory_outbox_store import (
    InMemoryOutboxStore,
)
from shell.platform.infrastructure.messaging.memory_outbox_store.outbox_record import OutboxRecord

__all__ = [
    "InMemoryOutboxStore",
    "OutboxRecord",
]
