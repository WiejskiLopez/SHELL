from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.sql import func

from shell.application.execution.workflow.dto.workflow import WorkflowDto
from shell.infrastructure.execution.workflow.persistence.sql.models import WorkflowModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class WorkflowQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, workflow_id: str) -> WorkflowDto | None:
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
                session_id=model.session_id,
                updated_at=model.updated_at,
                deleted_at=model.deleted_at,
            )

    async def list_all(
        self,
        *,
        page: int = 1,
        page_size: int = 100,
        status: str | None = None,
    ) -> tuple[list[WorkflowDto], int]:
        async with self._session_factory() as session:
            base_stmt = select(WorkflowModel)
            if status is not None:
                base_stmt = base_stmt.where(WorkflowModel.status == status)

            count_stmt = select(func.count()).select_from(base_stmt.subquery())
            total = (await session.execute(count_stmt)).scalar_one()

            offset = (page - 1) * page_size
            stmt = (
                base_stmt.order_by(WorkflowModel.created_at.desc()).offset(offset).limit(page_size)
            )
            rows = (await session.execute(stmt)).scalars().all()

            dtos = [
                WorkflowDto(
                    id=r.id,
                    status=r.status,
                    created_at=r.created_at,
                    session_id=r.session_id,
                    updated_at=r.updated_at,
                    deleted_at=r.deleted_at,
                )
                for r in rows
            ]
            return dtos, total
