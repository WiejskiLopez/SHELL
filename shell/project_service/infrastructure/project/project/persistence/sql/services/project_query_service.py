from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select
from sqlalchemy.sql import func

from shell.project_service.application.project.project.dto.project import ProjectDto
from shell.project_service.infrastructure.project.project.persistence.sql.models.project import (
    ProjectModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class ProjectQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, project_id: str) -> ProjectDto | None:
        async with self._session_factory() as session:
            stmt = select(ProjectModel).where(ProjectModel.id == project_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return ProjectDto(
                id=model.id,
                name=model.name,
                repo_url=model.repo_url,
                status=model.status,
                created_at=model.created_at,
                changed_at=model.changed_at,
                deleted_at=model.deleted_at,
            )

    async def list_all(
        self, *, page: int = 1, page_size: int = 100
    ) -> tuple[list[ProjectDto], int]:
        async with self._session_factory() as session:
            count_stmt = select(func.count()).select_from(ProjectModel)
            total = (await session.execute(count_stmt)).scalar_one()

            offset = (page - 1) * page_size
            stmt = (
                select(ProjectModel)
                .order_by(ProjectModel.created_at.desc())
                .offset(offset)
                .limit(page_size)
            )
            rows = (await session.execute(stmt)).scalars().all()

            dtos = [
                ProjectDto(
                    id=r.id,
                    name=r.name,
                    repo_url=r.repo_url,
                    status=r.status,
                    created_at=r.created_at,
                    changed_at=r.changed_at,
                    deleted_at=r.deleted_at,
                )
                for r in rows
            ]
            return dtos, total
