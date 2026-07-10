"""Event outbox/inbox SQLAlchemy models."""

from __future__ import annotations

from shell.platform.infrastructure.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.platform.infrastructure.persistence.sql.models.event.outbox_event import OutboxEventModel

__all__ = [
    "InboxEventModel",
    "OutboxEventModel",
]
