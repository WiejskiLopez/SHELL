"""Fresh baseline schema for the standalone User bounded context."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine

from shell.platform.infrastructure.persistence.sql.models.audit_event import AuditEventModel
from shell.platform.infrastructure.persistence.sql.models.base import Base
from shell.platform.infrastructure.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.platform.infrastructure.persistence.sql.models.event.outbox_event import OutboxEventModel
from shell.user.infrastructure.user.auth_session.persistence.sql.models.auth_session import (
    AuthSessionModel,
)
from shell.user.infrastructure.user.user.persistence.sql.models.user import UserModel
from shell.user.infrastructure.user.user_skill.persistence.sql.models.user_skill import (
    UserSkillModel,
)
from shell.user.infrastructure.user.user_state.persistence.sql.models.user_state import (
    UserStateModel,
)

_USER_TABLES = (
    UserModel.__table__,
    AuthSessionModel.__table__,
    UserSkillModel.__table__,
    UserStateModel.__table__,
    AuditEventModel.__table__,
    OutboxEventModel.__table__,
    InboxEventModel.__table__,
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
        await connection.run_sync(Base.metadata.create_all, tables=list(_USER_TABLES))
    await engine.dispose()
