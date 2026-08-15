"""Fresh baseline schema for the Session bounded context."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import create_async_engine

from shell.session_service.infrastructure.session.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
    InboxEventModel,
    OutboxEventModel,
    SessionSqlAlchemyModelBase,
)
from shell.session_service.infrastructure.session.session.persistence.sql.models.session import (
    SessionModel,
)
from shell.session_service.infrastructure.session.session_state.persistence.sql.models.session_state import (
    SessionStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy import Table

_TABLES: tuple[Table, ...] = cast(
    "tuple[Table, ...]",
    (
        SessionModel.__table__,
        SessionStateModel.__table__,
        PERSISTENCE_DELIVERY_MODELS.audit.__table__,
        OutboxEventModel.__table__,
        InboxEventModel.__table__,
        PERSISTENCE_DELIVERY_MODELS.messages.outbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.messages.inbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.commands.outbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.commands.inbox.__table__,
        PERSISTENCE_DELIVERY_MODELS.processed_delivery.__table__,
        PERSISTENCE_DELIVERY_MODELS.worker_heartbeat.__table__,
    ),
)


async def run_session_baseline(url: str) -> None:
    engine = create_async_engine(
        url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {}
    )
    async with engine.begin() as connection:
        await connection.run_sync(
            SessionSqlAlchemyModelBase.metadata.create_all, tables=list(_TABLES)
        )
    await engine.dispose()
