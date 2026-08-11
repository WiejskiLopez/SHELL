from __future__ import annotations

import importlib
import pkgutil

from sqlalchemy.ext.asyncio import create_async_engine

import shell.scheduling.infrastructure.scheduling as scheduling_infrastructure
from shell.platform.infrastructure.persistence.sql.models.audit_event import AuditEventModel
from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.platform.infrastructure.persistence.sql.models.event.outbox_event import OutboxEventModel


def _load_models() -> None:
    prefix = scheduling_infrastructure.__name__ + "."
    for module in pkgutil.walk_packages(scheduling_infrastructure.__path__, prefix):
        if ".models." in module.name:
            importlib.import_module(module.name)


async def run_scheduling_baseline(url: str) -> None:
    _load_models()
    tables_by_name = {
        table
        for table in Base.metadata.tables.values()
        if table.name in {"scheduler_definition", "scheduler_execution", "scheduler_job"}
    }
    tables_by_name.update({AuditEventModel.__table__, OutboxEventModel.__table__, InboxEventModel.__table__})
    engine = create_async_engine(url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {})
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all, tables=list(tables_by_name))
    await engine.dispose()
