from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.workflow.dto.workflow import WorkflowDto
    from shell.application.execution.workflow.ports.workflow_query_service import (
        WorkflowQueryService,
    )
    from shell.application.execution.workflow.queries.workflow_get_by_id_query import (
        WorkflowGetByIdQuery,
    )


class WorkflowGetByIdHandler:
    def __init__(self, queries: WorkflowQueryService) -> None:
        self._queries = queries

    async def handle(self, query: WorkflowGetByIdQuery) -> WorkflowDto | None:
        return await self._queries.get_workflow(query.workflow_id)
