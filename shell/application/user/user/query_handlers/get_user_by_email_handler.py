from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.user.user.dto.user import UserDto
    from shell.application.user.user.ports.user_query_service import UserQueryService
    from shell.application.user.user.queries.get_user_by_email_query import GetUserByEmailQuery


class GetUserByEmailHandler:
    def __init__(self, queries: UserQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetUserByEmailQuery) -> UserDto | None:
        return await self._queries.get_by_email(query.email)
