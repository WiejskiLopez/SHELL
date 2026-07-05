from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.domain.platform.value_objects.exists_result import ExistsResult
from shell.domain.project.aggregates.project.repositories.project_repository import (
    ProjectRepository,
)
from shell.infrastructure.project.persistence.sql.mappers import (
    project_entity_to_model,
    project_model_to_entity,
    project_update_model,
)

from ..models import ProjectModel

if TYPE_CHECKING:

    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.domain.project.aggregates.project.project import Project
    from shell.domain.project.value_objects.project_id import ProjectId


class SqlProjectRepository(ProjectRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: ProjectId) -> Project | None:
        query = select(ProjectModel).where(ProjectModel.id == project_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return project_model_to_entity(row) if row else None

    async def save(self, project: Project) -> None:
        model = await self._session.get(ProjectModel, project.id.value)
        if model is None:
            model = project_entity_to_model(project)
            self._session.add(model)
        else:
            project_update_model(model, project)

    async def delete(self, id: ProjectId) -> None:
        model = await self._session.get(ProjectModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: ProjectId) -> ExistsResult:
        query = select(ProjectModel).where(ProjectModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
