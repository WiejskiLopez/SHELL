from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import create_async_engine

from shell.ingestion.infrastructure.ingestion.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
    InboxEventModel,
    IngestionSqlAlchemyModelBase,
    OutboxEventModel,
)
from shell.ingestion.infrastructure.ingestion.persistence.sql.models.ingestion import (
    IngestionModel,
)

if TYPE_CHECKING:
    from sqlalchemy import Table

_TABLES: tuple[Table, ...] = cast(
    "tuple[Table, ...]",
    (
        IngestionModel.__table__,
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


async def run_ingestion_baseline(url: str) -> None:
    engine = create_async_engine(
        url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {}
    )
    async with engine.begin() as connection:
        await connection.run_sync(
            IngestionSqlAlchemyModelBase.metadata.create_all, tables=list(_TABLES)
        )
    await engine.dispose()
