from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution.application.execution.workflow.dto.workflow import WorkflowDto
    from shell.execution.application.execution.workflow.ports.workflow_query_service import (
        WorkflowQueryService,
    )
    from shell.execution.application.execution.workflow.queries.list_workflows_query import (
        ListWorkflowsQuery,
    )


class ListWorkflowsHandler:
    def __init__(self, queries: WorkflowQueryService) -> None:
        self._queries = queries

    async def handle(self, query: ListWorkflowsQuery) -> tuple[list[WorkflowDto], int]:
        return await self._queries.list_all(
            page=query.page, page_size=query.page_size, status=query.status
        )
