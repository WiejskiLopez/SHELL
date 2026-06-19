from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.dto import PromptDto
    from shell.application.platform.ports.queries import PromptQueryService
    from shell.application.platform.queries.queries import GetPromptQuery


class GetPromptHandler:
    def __init__(self, queries: PromptQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetPromptQuery) -> PromptDto | None:
        return await self._queries.get_prompt(query.name)
