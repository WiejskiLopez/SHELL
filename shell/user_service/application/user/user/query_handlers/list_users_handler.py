from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.user_service.application.user.user.dto.user_dto import UserDto
    from shell.user_service.application.user.user.ports.user_query_service import UserQueryService
    from shell.user_service.application.user.user.queries.list_users_query import ListUsersQuery


class ListUsersHandler:
    def __init__(self, queries: UserQueryService) -> None:
        self._queries = queries

    async def handle(self, query: ListUsersQuery) -> tuple[list[UserDto], int]:
        return await self._queries.list_all(page=query.page, page_size=query.page_size)
