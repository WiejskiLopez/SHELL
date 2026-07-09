from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.user.user_state.dto.user_state import UserStateDto
    from shell.application.user.user_state.ports.user_state_query_service import (
        UserStateQueryService,
    )
    from shell.application.user.user_state.queries.get_user_state_by_id_query import (
        GetUserStateByIdQuery,
    )


class GetUserStateByIdHandler:
    def __init__(self, queries: UserStateQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetUserStateByIdQuery) -> UserStateDto | None:
        return await self._queries.get_by_id(query.user_state_id)
