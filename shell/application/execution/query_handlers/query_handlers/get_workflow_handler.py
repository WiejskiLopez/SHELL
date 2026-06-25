from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.platform.dto import WorkflowDto
    from shell.application.platform.ports.queries import WorkflowQueryService
    from shell.application.platform.queries.queries import GetWorkflowQuery


class GetWorkflowHandler:
    def __init__(self, queries: WorkflowQueryService) -> None:
        self._queries = queries

    async def handle(self, get_workflow_query: GetWorkflowQuery) -> WorkflowDto | None:
        return await self._queries.get_workflow(get_workflow_query.workflow_id)
