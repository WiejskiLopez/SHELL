from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine

from shell.messaging.infrastructure.messaging.persistence.sql.models.base import (
    MessagingSqlAlchemyModelBase,
)
from shell.messaging.infrastructure.messaging.persistence.sql.models.message_router import (
    MessageRouterModel,
)
from shell.platform.infrastructure.persistence.sql.models.audit_event import AuditEventModel
from shell.platform.infrastructure.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.platform.infrastructure.persistence.sql.models.event.outbox_event import OutboxEventModel

_TABLES = (MessageRouterModel.__table__, AuditEventModel.__table__, OutboxEventModel.__table__, InboxEventModel.__table__)


async def run_messaging_baseline(url: str) -> None:
    engine = create_async_engine(url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {})
    async with engine.begin() as connection:
        await connection.run_sync(MessagingSqlAlchemyModelBase.metadata.create_all, tables=list(_TABLES))
    await engine.dispose()
