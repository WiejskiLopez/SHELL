"""Fresh baseline schema for the Session bounded context."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine

from shell.platform.infrastructure.persistence.sql.models.audit_event import AuditEventModel
from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.platform.infrastructure.persistence.sql.models.event.outbox_event import OutboxEventModel
from shell.session.infrastructure.session.session.persistence.sql.models.session import SessionModel
from shell.session.infrastructure.session.session_state.persistence.sql.models.session_state import (
    SessionStateModel,
)

_TABLES = (
    SessionModel.__table__,
    SessionStateModel.__table__,
    AuditEventModel.__table__,
    OutboxEventModel.__table__,
    InboxEventModel.__table__,
)


async def run_session_baseline(url: str) -> None:
    engine = create_async_engine(url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {})
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=list(_TABLES))
    await engine.dispose()
