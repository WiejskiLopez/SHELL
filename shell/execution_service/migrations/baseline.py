from __future__ import annotations

import importlib
import pkgutil
from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import create_async_engine

import shell.execution_service.infrastructure.execution as execution_infrastructure
from shell.execution_service.infrastructure.execution.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
    ExecutionSqlAlchemyModelBase,
    InboxEventModel,
    OutboxEventModel,
)

if TYPE_CHECKING:
    from sqlalchemy import Table


def _load_models() -> None:
    prefix = execution_infrastructure.__name__ + "."
    for module in pkgutil.walk_packages(execution_infrastructure.__path__, prefix):
        if ".models." in module.name:
            importlib.import_module(module.name)


async def run_execution_baseline(url: str) -> None:
    _load_models()
    tables_by_name: set[Table] = {
        table
        for table in ExecutionSqlAlchemyModelBase.metadata.tables.values()
        if table.name not in {"user", "auth_sessions", "session", "project"}
    }
    tables_by_name.update(
        cast(
            "set[Table]",
            {
                PERSISTENCE_DELIVERY_MODELS.audit.__table__,
                OutboxEventModel.__table__,
                InboxEventModel.__table__,
                PERSISTENCE_DELIVERY_MODELS.messages.outbox.__table__,
                PERSISTENCE_DELIVERY_MODELS.messages.inbox.__table__,
                PERSISTENCE_DELIVERY_MODELS.commands.outbox.__table__,
                PERSISTENCE_DELIVERY_MODELS.commands.inbox.__table__,
                PERSISTENCE_DELIVERY_MODELS.processed_delivery.__table__,
                PERSISTENCE_DELIVERY_MODELS.worker_heartbeat.__table__,
            },
        )
    )
    engine = create_async_engine(
        url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {}
    )
    async with engine.begin() as connection:
        await connection.run_sync(
            ExecutionSqlAlchemyModelBase.metadata.create_all, tables=list(tables_by_name)
        )
    await engine.dispose()
