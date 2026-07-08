from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.application.project.project.dto.project import ProjectDto
from shell.infrastructure.project.project.persistence.sql.models.project import ProjectModel

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
                updated_at=model.updated_at,
                deleted_at=model.deleted_at,
            )
