from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.messaging.dto.message_router import MessageRouterDto
    from shell.application.messaging.ports.queries.message_router_query_service import (
        MessageRouterQueryService,
    )
    from shell.application.messaging.queries.get_message_by_id_query import GetMessageByIdQuery


class GetMessageByIdHandler:
    def __init__(self, queries: MessageRouterQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetMessageByIdQuery) -> MessageRouterDto | None:
        return await self._queries.get_by_id(query.message_id)  # type: ignore[arg-type]
