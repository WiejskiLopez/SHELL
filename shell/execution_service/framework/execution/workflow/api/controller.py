from __future__ import annotations

from fastapi import HTTPException

from shell.execution_service.application.execution.workflow.commands.change_workflow_command import (
    ChangeWorkflowCommand,
)
from shell.execution_service.application.execution.workflow.commands.create_workflow_command import (
    CreateWorkflowCommand,
)
from shell.execution_service.application.execution.workflow.commands.delete_workflow_command import (
    DeleteWorkflowCommand,
)
from shell.execution_service.application.execution.workflow.queries.get_workflow_by_id_query import (
    GetWorkflowByIdQuery,
)
from shell.execution_service.application.execution.workflow.queries.list_workflows_query import (
    ListWorkflowsQuery,
)
from shell.execution_service.framework.execution.workflow.api.change_workflow_request import (
    ChangeWorkflowRequest as ApiChangeWorkflowRequest,
)
from shell.execution_service.framework.execution.workflow.api.create_workflow_request import (
    CreateWorkflowRequest as ApiCreateWorkflowRequest,
)
from shell.execution_service.framework.execution.workflow.api.create_workflow_response import (
    CreateWorkflowResponse as ApiCreateWorkflowResponse,
)
from shell.execution_service.framework.execution.workflow.api.workflow_response import (
    WorkflowResponse as ApiWorkflowResponse,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.models.page import Page


class WorkflowController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(self, command_bus: CommandBus, query_bus: QueryBus) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def list_workflows(
        self, page: int = 1, page_size: int = 100, status: str | None = None
    ) -> Page[ApiWorkflowResponse]:
        dtos, total = await self._query_bus.dispatch(
            ListWorkflowsQuery(page=page, page_size=page_size, status=status)
        )
        items = [
            ApiWorkflowResponse(
                id=d.id,
                status=d.status,
                session_id=d.session_id,
                project_id=d.project_id,
                created_at=d.created_at,
                changed_at=d.changed_at,
                deleted_at=d.deleted_at,
            )
            for d in dtos
        ]
        has_more = (page * page_size) < total
        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    async def get_workflow(self, workflow_id: str) -> ApiWorkflowResponse:
        result = await self._query_bus.dispatch(GetWorkflowByIdQuery(workflow_id=workflow_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
        return ApiWorkflowResponse(
            id=result.id,
            status=result.status,
            session_id=result.session_id,
            project_id=result.project_id,
            created_at=result.created_at,
            changed_at=result.changed_at,
            deleted_at=result.deleted_at,
        )

    async def create_workflow(self, body: ApiCreateWorkflowRequest) -> ApiCreateWorkflowResponse:
        workflow_id = await self._command_bus.dispatch(
            CreateWorkflowCommand(session_id=body.session_id, project_id=body.project_id)
        )
        return ApiCreateWorkflowResponse(id=workflow_id)

    async def change_workflow(self, workflow_id: str, body: ApiChangeWorkflowRequest) -> None:
        try:
            await self._command_bus.dispatch(ChangeWorkflowCommand(workflow_id=workflow_id))
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
