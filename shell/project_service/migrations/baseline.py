from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import create_async_engine

from shell.project_service.infrastructure.project.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
    InboxEventModel,
    OutboxEventModel,
    ProjectSqlAlchemyModelBase,
)
from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
    ProjectModel,
)
from shell.project_service.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
    ProjectSkillModel,
)
from shell.project_service.infrastructure.project.project_state.persistence.sql.models.project_state import (
    ProjectStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy import Table

_TABLES: tuple[Table, ...] = cast(
    "tuple[Table, ...]",
    (
        ProjectModel.__table__,
        ProjectSkillModel.__table__,
        ProjectStateModel.__table__,
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


async def run_project_baseline(url: str, reset_db: bool = False) -> None:
    engine = create_async_engine(
        url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {}
    )
    async with engine.begin() as connection:
        if reset_db:
            await connection.run_sync(
                ProjectSqlAlchemyModelBase.metadata.drop_all, tables=list(_TABLES)
            )
        await connection.run_sync(
            ProjectSqlAlchemyModelBase.metadata.create_all, tables=list(_TABLES)
        )
    await engine.dispose()
