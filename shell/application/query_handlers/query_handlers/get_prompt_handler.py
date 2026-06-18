from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.dto.dto import PromptDto
    from shell.application.ports.queries import PromptQueryService
    from shell.application.queries.queries import GetPromptQuery


class GetPromptHandler:
    def __init__(self, queries: PromptQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetPromptQuery) -> PromptDto | None:
        return await self._queries.get_prompt(query.name)
