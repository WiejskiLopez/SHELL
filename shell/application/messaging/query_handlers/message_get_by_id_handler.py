from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.messaging.dto.message import MessageDto
    from shell.application.messaging.ports.queries.message_query_service import MessageQueryService
    from shell.application.messaging.queries.message_get_by_id_query import MessageGetByIdQuery


class MessageGetByIdHandler:
    def __init__(self, queries: MessageQueryService) -> None:
        self._queries = queries

    async def handle(self, query: MessageGetByIdQuery) -> MessageDto | None:
        return await self._queries.get_by_id(query.message_id)  # type: ignore[arg-type]
