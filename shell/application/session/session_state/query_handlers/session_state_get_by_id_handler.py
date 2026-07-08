from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.session.session_state.dto.session_state import SessionStateDto
    from shell.application.session.session_state.ports.session_state_query_service import (
        SessionStateQueryService,
    )
    from shell.application.session.session_state.queries.session_state_get_by_id_query import (
        SessionStateGetByIdQuery,
    )


class SessionStateGetByIdHandler:
    def __init__(self, queries: SessionStateQueryService) -> None:
        self._queries = queries

    async def handle(self, query: SessionStateGetByIdQuery) -> SessionStateDto | None:
        return await self._queries.get_by_id(query.session_state_id)
