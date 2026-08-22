"""Message outbox/inbox messaging services."""

from __future__ import annotations

from shell.platform.infrastructure.messaging.message.sql_message_outbox_publisher import (
    SqlMessageOutboxPublisher,
)

__all__ = ["SqlMessageOutboxPublisher"]
