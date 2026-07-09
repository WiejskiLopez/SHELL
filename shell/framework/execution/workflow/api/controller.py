from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.execution.workflow.queries.get_workflow_by_id_query import (
    GetWorkflowByIdQuery,
)

if TYPE_CHECKING:
    from shell.application.platform.bus.query_bus import QueryBus


class WorkflowController:
    __slots__ = ("_query_bus",)

    def __init__(self, query_bus: QueryBus) -> None:
        self._query_bus = query_bus

    async def get_workflow(self, workflow_id: str) -> dict:
        result = await self._query_bus.dispatch(GetWorkflowByIdQuery(workflow_id=workflow_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        return {"workflow_id": workflow_id, "workflow": str(result)}
