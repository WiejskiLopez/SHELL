from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.session.application.session.session.dto.session import SessionDto
    from shell.session.application.session.session.ports.session_query_service import (
        SessionQueryService,
    )
    from shell.session.application.session.session.queries.list_sessions_query import (
        ListSessionsQuery,
    )


class ListSessionsHandler:
    def __init__(self, queries: SessionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: ListSessionsQuery) -> tuple[list[SessionDto], int]:
        return await self._queries.list_all(
            page=query.page,
            page_size=query.page_size,
            user_id=query.user_id,
        )
