from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.user.user_state.dto.user_state import UserStateDto
    from shell.application.user.user_state.ports.user_state_query_service import (
        UserStateQueryService,
    )
    from shell.application.user.user_state.queries.user_state_get_by_id_query import (
        UserStateGetByIdQuery,
    )


class UserStateGetByIdHandler:
    def __init__(self, queries: UserStateQueryService) -> None:
        self._queries = queries

    async def handle(self, query: UserStateGetByIdQuery) -> UserStateDto | None:
        return await self._queries.get_by_id(query.user_state_id)
