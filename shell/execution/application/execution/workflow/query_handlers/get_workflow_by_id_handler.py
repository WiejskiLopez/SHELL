from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.execution.application.execution.workflow.dto.workflow import WorkflowDto
    from shell.execution.application.execution.workflow.ports.workflow_query_service import (
        WorkflowQueryService,
    )
    from shell.execution.application.execution.workflow.queries.get_workflow_by_id_query import (
        GetWorkflowByIdQuery,
    )


class GetWorkflowByIdHandler:
    def __init__(self, queries: WorkflowQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetWorkflowByIdQuery) -> WorkflowDto | None:
        return await self._queries.get_by_id(query.workflow_id)
