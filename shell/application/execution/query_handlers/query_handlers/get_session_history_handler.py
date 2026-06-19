from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.dto import SessionDto
    from shell.application.platform.ports.queries import SessionQueryService
    from shell.application.platform.queries.queries import GetSessionHistoryQuery


class GetSessionHistoryHandler:
    def __init__(self, queries: SessionQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetSessionHistoryQuery) -> SessionDto | None:
        return await self._queries.get_session_history(query.session_id)
