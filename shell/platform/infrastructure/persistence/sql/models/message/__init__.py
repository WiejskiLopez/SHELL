"""Message outbox/inbox SQLAlchemy models."""

from __future__ import annotations

from shell.platform.infrastructure.persistence.sql.models.message.inbox_message import (
    InboxMessageModel,
)
from shell.platform.infrastructure.persistence.sql.models.message.outbox_message import (
    OutboxMessageModel,
)

__all__ = [
    "OutboxMessageModel",
    "InboxMessageModel",
]
