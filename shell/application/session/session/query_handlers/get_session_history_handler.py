from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.session.session.dto.session import SessionDto
    from shell.application.session.session.ports.session_query_service import (
        SessionQueryService,
    )
    from shell.application.session.session.queries.get_session_history_query import (
        GetSessionHistoryQuery,
    )


class GetSessionHistoryHandler:
    def __init__(self, queries: SessionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetSessionHistoryQuery) -> SessionDto | None:
        return await self._queries.get_by_id(query.session_id)
