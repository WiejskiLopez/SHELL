from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import select

from shell.platform.domain.value_objects.exists_result import ExistsResult
from shell.user.domain.user.aggregates.user_skill.repositories.user_skill_repository import (
    UserSkillRepository,
)
from shell.user.infrastructure.user.user_skill.persistence.sql.mappers import (
    user_skill_entity_to_model,
    user_skill_model_to_entity,
)

from ..models import UserSkillModel

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

    from shell.user.domain.user.aggregates.user_skill.user_skill import UserSkill
    from shell.user.domain.user.aggregates.user_skill.value_objects.user_skill_id import UserSkillId
    from shell.user.domain.user.value_objects.user_id import UserId


class SqlUserSkillRepository(UserSkillRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, skill_id: UserSkillId) -> UserSkill | None:
        query = select(UserSkillModel).where(UserSkillModel.id == skill_id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return user_skill_model_to_entity(row) if row else None

    async def get_by_user_id(self, user_id: UserId) -> list[UserSkill]:
        query = select(UserSkillModel).where(UserSkillModel.user_id == user_id.value)
        rows = (await self._session.execute(query)).scalars().all()
        return [user_skill_model_to_entity(row) for row in rows]

    async def save(self, user_skill: UserSkill) -> None:
        model = await self._session.get(UserSkillModel, user_skill.id.value)
        if model is None:
            model = user_skill_entity_to_model(user_skill)
            self._session.add(model)
        else:
            model.skill_data = json.dumps(json.loads(user_skill.skill_data.value.value))  # type: ignore[assignment]

    async def delete(self, id: UserSkillId, now: datetime | None = None) -> None:
        if now is None:
            now = datetime.now(tz=UTC)
        model = await self._session.get(UserSkillModel, id.value)
        if model is not None:
            model.deleted_at = now

    async def exists(self, id: UserSkillId) -> ExistsResult:
        query = select(UserSkillModel).where(UserSkillModel.id == id.value)
        row = (await self._session.execute(query)).scalar_one_or_none()
        return ExistsResult(row is not None)
