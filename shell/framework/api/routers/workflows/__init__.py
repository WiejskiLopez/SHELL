"""Workflows router — start and query workflows."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as _Request
from pydantic import BaseModel

from shell.application.commands.commands import RouteEnvelopesCommand, StartWorkflowCommand
from shell.application.queries.queries import GetWorkflowQuery
from shell.framework.api.routers.workflows.start_workflow_request import StartWorkflowRequest
from shell.framework.api.routers.workflows.start_workflow_response import StartWorkflowResponse
from shell.framework.api.routers.workflows.route_response import RouteResponse

if TYPE_CHECKING:
    from shell.application.bus.command_bus import CommandBus
    from shell.application.bus.query_bus import QueryBus
    from shell.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


def get_command_bus(container: CoreContainer = Depends(get_core_container)) -> CommandBus:
    return container.app.buses.command_bus()  # type: ignore[attr-defined, no-any-return]


def get_query_bus(container: CoreContainer = Depends(get_core_container)) -> QueryBus:
    return container.app.buses.query_bus()  # type: ignore[attr-defined, no-any-return]


@router.post("", response_model=StartWorkflowResponse, status_code=201)
async def start_workflow(
    start_workflow_request: StartWorkflowRequest,
    command_bus: CommandBus = Depends(get_command_bus),
) -> StartWorkflowResponse:
    cmd = StartWorkflowCommand(task_execution_id=start_workflow_request.task_execution_id)
    wf_id = await command_bus.dispatch(cmd)
    return StartWorkflowResponse(workflow_id=str(wf_id))


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    query_bus: QueryBus = Depends(get_query_bus),
) -> dict:
    result = await query_bus.dispatch(GetWorkflowQuery(workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return {"workflow_id": workflow_id, "workflow": str(result)}


@router.post("/{workflow_id}/route", response_model=RouteResponse)
async def route_envelopes(
    workflow_id: str, command_bus: CommandBus = Depends(get_command_bus)
) -> RouteResponse:
    cmd = RouteEnvelopesCommand(workflow_id=workflow_id)
    count = await command_bus.dispatch(cmd)
    return RouteResponse(routed=count or 0)
