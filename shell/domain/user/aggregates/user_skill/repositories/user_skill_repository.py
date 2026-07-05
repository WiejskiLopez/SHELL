from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.platform.value_objects.exists_result import ExistsResult
    from shell.domain.user.aggregates.user_skill.user_skill import UserSkill
    from shell.domain.user.value_objects.skill_id import SkillId
    from shell.domain.user.value_objects.user_id import UserId


class UserSkillRepository(Protocol):
    async def get_by_id(self, skill_id: SkillId) -> UserSkill | None: ...
    async def get_by_user_id(self, user_id: UserId) -> list[UserSkill]: ...
    async def save(self, user_skill: UserSkill) -> None: ...
    async def delete(self, id: SkillId) -> None: ...
    async def exists(self, id: SkillId) -> ExistsResult: ...
