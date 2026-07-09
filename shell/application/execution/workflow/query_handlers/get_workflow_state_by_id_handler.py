from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.workflow.dto.workflow_state import WorkflowStateDto
    from shell.application.execution.workflow.ports.workflow_state_query_service import (
        WorkflowStateQueryService,
    )
    from shell.application.execution.workflow.queries.get_workflow_state_by_id_query import (
        GetWorkflowStateByIdQuery,
    )


class GetWorkflowStateByIdHandler:
    def __init__(self, queries: WorkflowStateQueryService) -> None:
        self._queries = queries

    async def handle(self, query: GetWorkflowStateByIdQuery) -> WorkflowStateDto | None:
        return await self._queries.get_by_id(query.workflow_state_id)
