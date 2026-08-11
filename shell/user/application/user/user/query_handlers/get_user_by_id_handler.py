from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.user.application.user.user.dto.user import UserDto
    from shell.user.application.user.user.ports.user_query_service import UserQueryService
    from shell.user.application.user.user.queries.get_user_by_id_query import GetUserByIdQuery


class GetUserByIdHandler:
    def __init__(self, queries: UserQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetUserByIdQuery) -> UserDto | None:
        return await self._queries.get_by_id(query.user_id)
