from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.user.application.user.user_skill.dto.user_skill import UserSkillDto
    from shell.user.application.user.user_skill.ports.user_skill_query_service import (
        UserSkillQueryService,
    )
    from shell.user.application.user.user_skill.queries.get_user_skill_by_id_query import (
        GetUserSkillByIdQuery,
    )


class GetUserSkillByIdHandler:
    def __init__(self, queries: UserSkillQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetUserSkillByIdQuery) -> UserSkillDto | None:
        return await self._queries.get_by_id(query.user_skill_id)
