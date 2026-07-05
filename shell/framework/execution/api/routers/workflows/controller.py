from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.execution.commands.workflow_commands import StartWorkflowCommand
from shell.application.execution.queries.workflow_get_by_id_query import WorkflowGetByIdQuery
from shell.framework.execution.api.routers.workflows.start_workflow_response import (
    StartWorkflowResponse,
)

if TYPE_CHECKING:
    from shell.application.platform.bus.command_bus import CommandBus
    from shell.application.platform.bus.query_bus import QueryBus


class WorkflowController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def start_workflow(self, task_execution_id: str) -> StartWorkflowResponse:
        command = StartWorkflowCommand(task_execution_id=task_execution_id)
        workflow_id = await self._command_bus.dispatch(command)
        return StartWorkflowResponse(workflow_id=str(workflow_id))

    async def get_workflow(self, workflow_id: str) -> dict:
        result = await self._query_bus.dispatch(WorkflowGetByIdQuery(workflow_id=workflow_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        return {"workflow_id": workflow_id, "workflow": str(result)}
