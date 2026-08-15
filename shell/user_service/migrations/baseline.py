"""Fresh baseline schema for the standalone User bounded context."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from sqlalchemy.ext.asyncio import create_async_engine

from shell.user_service.infrastructure.user.auth_session.persistence.sql.models.auth_session import (
    AuthSessionModel,
)
from shell.user_service.infrastructure.user.persistence.sql.models.base import (
    PERSISTENCE_DELIVERY_MODELS,
    InboxEventModel,
    OutboxEventModel,
    UserSqlAlchemyModelBase,
)
from shell.user_service.infrastructure.user.user.persistence.sql.models.user import UserModel
from shell.user_service.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
    UserSkillModel,
)
from shell.user_service.infrastructure.user.user_state.persistence.sql.models.user_state import (
    UserStateModel,
)

if TYPE_CHECKING:
    from sqlalchemy import Table

_USER_TABLES: tuple[Table, ...] = cast(
    "tuple[Table, ...]",
    (
        UserModel.__table__,
        AuthSessionModel.__table__,
        UserSkillModel.__table__,
        UserStateModel.__table__,
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


async def run_user_baseline(url: str) -> None:
    """Create the current User schema on a fresh database.

    This intentionally creates a new baseline for the standalone User BC.
    migration history. Existing databases require an explicit data migration.
    """
    engine = create_async_engine(
        url,
        future=True,
        connect_args={"check_same_thread": False} if "sqlite" in url else {},
    )
    async with engine.begin() as connection:
        await connection.run_sync(
            UserSqlAlchemyModelBase.metadata.create_all, tables=list(_USER_TABLES)
        )
    await engine.dispose()
