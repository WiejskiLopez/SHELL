"""Event outbox/inbox SQLAlchemy models."""

from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.infrastructure.platform.persistence.sql.models.event.outbox_event import OutboxEventModel

__all__ = [
    "InboxEventModel",
    "OutboxEventModel",
]
