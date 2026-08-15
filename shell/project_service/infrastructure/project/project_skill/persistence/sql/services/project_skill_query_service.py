from __future__ import annotations

import json
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.types import JsonStr
from shell.project_service.application.project.project_skill.dto.project_skill import (
    ProjectSkillDto,
)
from shell.project_service.infrastructure.project.project_skill.persistence.sql.models.project_skill import (
    ProjectSkillModel,
)

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class ProjectSkillQueryService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def get_by_id(self, project_skill_id: str) -> ProjectSkillDto | None:
        async with self._session_factory() as session:
            stmt = select(ProjectSkillModel).where(ProjectSkillModel.id == project_skill_id)
            res = await session.execute(stmt)
            model = res.scalar_one_or_none()
            if not model:
                return None
            return ProjectSkillDto(
                id=model.id,
                project_id=model.project_id,
                skill_data=JsonStr(json.dumps(dict(model.skill_data))),
                created_at=model.created_at,
                changed_at=model.changed_at,
            )
