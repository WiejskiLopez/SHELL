from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.platform.domain.value_objects.exists_result import ExistsResult
    from shell.user_service.domain.user.aggregates.user_skill.user_skill import UserSkill
    from shell.user_service.domain.user.aggregates.user_skill.value_objects.user_skill_id import (
        UserSkillId,
    )
    from shell.user_service.domain.user.value_objects.user_id import UserId


class UserSkillRepository(Protocol):
    async def get_by_id(self, skill_id: UserSkillId) -> UserSkill | None: ...
    async def get_by_user_id(self, user_id: UserId) -> list[UserSkill]: ...
    async def save(self, user_skill: UserSkill) -> None: ...
    async def delete(self, id: UserSkillId) -> None: ...
    async def exists(self, id: UserSkillId) -> ExistsResult: ...
