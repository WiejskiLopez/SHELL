from __future__ import annotations

from typing import TYPE_CHECKING

from shell.application.platform.dto import WorkflowDto
from shell.infrastructure.execution.persistence.sql.models import WorkflowModel
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class WorkflowQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_workflow(self, workflow_id: str) -> WorkflowDto | None:
        async with self._session_factory() as session:
            stmt = select(WorkflowModel).where(WorkflowModel.id == workflow_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return WorkflowDto(
                id=model.id,
                status=model.status,
                created_at=model.created_at,
            )
