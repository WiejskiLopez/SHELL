"""Command outbox/inbox SQLAlchemy models."""

from __future__ import annotations

from shell.platform.infrastructure.persistence.sql.models.command.inbox_command import (
    InboxCommandModel,
)
from shell.platform.infrastructure.persistence.sql.models.command.outbox_command import (
    OutboxCommandModel,
)

__all__ = [
    "InboxCommandModel",
    "OutboxCommandModel",
]
