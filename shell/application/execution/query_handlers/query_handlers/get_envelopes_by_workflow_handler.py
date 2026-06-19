from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.dto import EnvelopeDto
    from shell.application.platform.ports.queries import EnvelopeQueryService
    from shell.application.platform.queries.queries import GetEnvelopesByWorkflowQuery


class GetEnvelopesByWorkflowHandler:
    def __init__(self, queries: EnvelopeQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetEnvelopesByWorkflowQuery) -> list[EnvelopeDto]:
        return await self._queries.get_envelopes_by_workflow(query.workflow_id, query.pending_only)
