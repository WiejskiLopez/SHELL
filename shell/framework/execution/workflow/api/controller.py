from __future__ import annotations

from fastapi import HTTPException

from shell.application.execution.workflow.commands.create_workflow_command import (
    CreateWorkflowCommand,
)
from shell.application.execution.workflow.commands.delete_workflow_command import (
    DeleteWorkflowCommand,
)
from shell.application.execution.workflow.commands.update_workflow_command import (
    UpdateWorkflowCommand,
)
from shell.application.execution.workflow.queries.get_workflow_by_id_query import (
    GetWorkflowByIdQuery,
)
from shell.framework.execution.workflow.api.create_workflow_request import (
    CreateWorkflowRequest as ApiCreateWorkflowRequest,
)
from shell.framework.execution.workflow.api.create_workflow_response import (
    CreateWorkflowResponse as ApiCreateWorkflowResponse,
)
from shell.framework.execution.workflow.api.update_workflow_request import (
    UpdateWorkflowRequest as ApiUpdateWorkflowRequest,
)
from shell.framework.execution.workflow.api.workflow_response import (
    WorkflowResponse as ApiWorkflowResponse,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus


class WorkflowController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_workflow(self, workflow_id: str) -> ApiWorkflowResponse:
        result = await self._query_bus.dispatch(GetWorkflowByIdQuery(workflow_id=workflow_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        return ApiWorkflowResponse(
            id=result.id,
            status=result.status,
            session_id=result.session_id,
            created_at=result.created_at,
            updated_at=result.updated_at,
            deleted_at=result.deleted_at,
        )

    async def create_workflow(self, body: ApiCreateWorkflowRequest) -> ApiCreateWorkflowResponse:
        workflow_id = await self._command_bus.dispatch(
            CreateWorkflowCommand(session_id=body.session_id)
        )
        return ApiCreateWorkflowResponse(id=workflow_id)

    async def update_workflow(self, workflow_id: str, body: ApiUpdateWorkflowRequest) -> None:
        try:
            await self._command_bus.dispatch(UpdateWorkflowCommand(workflow_id=workflow_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_workflow(self, workflow_id: str) -> None:
        try:
            await self._command_bus.dispatch(DeleteWorkflowCommand(workflow_id=workflow_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
