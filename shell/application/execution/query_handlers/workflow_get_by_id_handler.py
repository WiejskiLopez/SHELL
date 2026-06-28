from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shell.application.execution.dto.workflow import WorkflowDto
    from shell.application.platform.ports.queries import WorkflowQueryService
    from shell.application.execution.queries.workflow_get_by_id_query import WorkflowGetByIdQuery


class WorkflowGetByIdHandler:
    def __init__(self, queries: WorkflowQueryService) -> None:
        self._queries = queries

    async def handle(self, get_workflow_query: WorkflowGetByIdQuery) -> WorkflowDto | None:
        return await self._queries.get_workflow(get_workflow_query.workflow_id)
