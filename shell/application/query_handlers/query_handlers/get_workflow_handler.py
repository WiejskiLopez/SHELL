from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.dto import WorkflowDto
    from shell.application.ports.queries import WorkflowQueryService
    from shell.application.queries.queries import GetWorkflowQuery


class GetWorkflowHandler:
    def __init__(self, queries: WorkflowQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetWorkflowQuery) -> WorkflowDto | None:
        return await self._queries.get_workflow(query.workflow_id)
