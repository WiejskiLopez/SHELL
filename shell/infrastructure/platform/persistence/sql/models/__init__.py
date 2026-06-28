"""SQLAlchemy ORM models — platform shared kernel."""

from __future__ import annotations

from shell.infrastructure.platform.persistence.sql.models.audit_event import AuditEventModel
from shell.infrastructure.platform.persistence.sql.models.base import Base
from shell.infrastructure.platform.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.infrastructure.platform.persistence.sql.models.event.outbox_event import OutboxEventModel
from shell.infrastructure.platform.persistence.sql.models.message.inbox_message import InboxMessageModel
from shell.infrastructure.platform.persistence.sql.models.message.message import MessageModel
from shell.infrastructure.platform.persistence.sql.models.message.outbox_message import OutboxMessageModel

__all__ = [
    "AuditEventModel",
    "Base",
    "InboxEventModel",
    "InboxMessageModel",
    "MessageModel",
    "OutboxEventModel",
    "OutboxMessageModel",
]
