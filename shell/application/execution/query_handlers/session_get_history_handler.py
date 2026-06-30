from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.queries.session_get_history_query import SessionGetHistoryQuery
    from shell.application.platform.ports.queries import SessionQueryService
    from shell.application.session.dto.session import SessionDto


class SessionGetHistoryHandler:
    def __init__(self, queries: SessionQueryService) -> None:
        self._queries = queries

    async def handle(self, get_session_history_query: SessionGetHistoryQuery) -> SessionDto | None:
        return await self._queries.get_session_history(get_session_history_query.session_id)
