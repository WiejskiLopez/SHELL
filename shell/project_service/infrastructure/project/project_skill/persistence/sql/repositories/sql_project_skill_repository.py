from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.project_service.domain.project.aggregates.project_skill.repositories.project_skill_repository import (
    ProjectSkillRepository,
)
from shell.project_service.infrastructure.project.project_skill.persistence.sql.mappers import (
    project_skill_entity_to_model,
    project_skill_model_to_entity,
)

from ..models import ProjectSkillModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.project_service.domain.project.aggregates.project.value_objects.project_id import (
        ProjectId,
    )
    from shell.project_service.domain.project.aggregates.project_skill.project_skill import (
        ProjectSkill,
    )
    from shell.project_service.domain.project.aggregates.project_skill.value_objects.project_skill_id import (
        ProjectSkillId,
    )


class SqlProjectSkillRepository(ProjectSkillRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, skill_id: ProjectSkillId) -> ProjectSkill | None:
        query = select(ProjectSkillModel).where(ProjectSkillModel.id == skill_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return project_skill_model_to_entity(row) if row else None

    async def get_by_project_id(self, project_id: ProjectId) -> list[ProjectSkill]:
        query = select(ProjectSkillModel).where(ProjectSkillModel.project_id == project_id.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [project_skill_model_to_entity(row) for row in rows]

    async def save(self, project_skill: ProjectSkill) -> None:
        model = await self._session.get(ProjectSkillModel, project_skill.id.value)
        if model is None:
            model = project_skill_entity_to_model(project_skill)
            self._session.add(model)
        else:
            model.skill_data = json.dumps(json.loads(project_skill.skill_data.value.value))  # type: ignore[assignment]
            model.changed_at = project_skill.changed_at.value

    async def delete(self, id: ProjectSkillId) -> None:
        model = await self._session.get(ProjectSkillModel, id.value)
        if model is not None:
            await self._session.delete(model)

    async def exists(self, id: ProjectSkillId) -> ExistsResult:
        query = select(ProjectSkillModel).where(ProjectSkillModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
