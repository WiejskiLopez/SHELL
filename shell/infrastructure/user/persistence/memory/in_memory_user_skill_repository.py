from __future__ import annotations

from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user_skill.repositories.user_skill_repository import (
    UserSkillRepository,
)
from shell.domain.user.aggregates.user_skill.user_skill import UserSkill
from shell.domain.user.value_objects.skill_id import SkillId
from shell.infrastructure.platform.persistence.in_memory_repository import InMemoryRepository

if TYPE_CHECKING:
    from shell.domain.user.value_objects.user_id import UserId


class InMemoryUserSkillRepository(InMemoryRepository[UserSkill, SkillId], UserSkillRepository):
    async def get_by_user_id(self, user_id: UserId) -> list[UserSkill]:
        return [
            skill for skill in self._store.values() if skill.user_id == user_id
        ]
