from __future__ import annotations

from sqlalchemy.ext.asyncio import create_async_engine

from shell.platform.infrastructure.persistence.sql.models.audit_event import AuditEventModel
from shell.platform.infrastructure.persistence.sql.models.event.inbox_event import InboxEventModel
from shell.platform.infrastructure.persistence.sql.models.event.outbox_event import OutboxEventModel
from shell.project.infrastructure.project.persistence.sql.models.base import (
    ProjectSqlAlchemyModelBase,
)
from shell.project.infrastructure.project.project.persistence.sql.models.project import ProjectModel
from shell.project.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
    ProjectSkillModel,
)
from shell.project.infrastructure.project.project_state.persistence.sql.models.project_state import (
    ProjectStateModel,
)

_TABLES = (ProjectModel.__table__, ProjectSkillModel.__table__, ProjectStateModel.__table__, AuditEventModel.__table__, OutboxEventModel.__table__, InboxEventModel.__table__)


async def run_project_baseline(url: str) -> None:
    engine = create_async_engine(url, future=True, connect_args={"check_same_thread": False} if "sqlite" in url else {})
    async with engine.begin() as connection:
        await connection.run_sync(ProjectSqlAlchemyModelBase.metadata.create_all, tables=list(_TABLES))
    await engine.dispose()
