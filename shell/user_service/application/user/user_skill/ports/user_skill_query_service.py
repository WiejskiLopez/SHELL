from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.user_service.application.user.user_skill.dto.user_skill import UserSkillDto


class UserSkillQueryService(Protocol):
    async def get_by_id(self, user_skill_id: str) -> UserSkillDto | None: ...
