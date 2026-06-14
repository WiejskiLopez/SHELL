"""Workflows router — start and query workflows."""
from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException
from fastapi import Request as _Request
from pydantic import BaseModel

from shell_ddd.application.commands.commands import RouteEnvelopesCommand, StartWorkflowCommand
from shell_ddd.application.queries.queries import GetWorkflowQuery

if TYPE_CHECKING:
    from shell_ddd.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/workflows", tags=["workflows"])


class StartWorkflowRequest(BaseModel):
    task_name: str


class StartWorkflowResponse(BaseModel):
    workflow_id: str


class RouteResponse(BaseModel):
    routed: int


def get_core_container(request: _Request) -> CoreContainer:
    return request.app.state.core_container


@router.post("", response_model=StartWorkflowResponse, status_code=201)
async def start_workflow(
    body: StartWorkflowRequest, core_container: CoreContainer = Depends(get_core_container)
) -> StartWorkflowResponse:
    cmd = StartWorkflowCommand(task_name=body.task_name)
    wf_id = await core_container.app.buses.command_bus().dispatch(cmd)
    return StartWorkflowResponse(workflow_id=str(wf_id))


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str, core_container: CoreContainer = Depends(get_core_container)) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(GetWorkflowQuery(workflow_id=workflow_id))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{workflow_id}' not found")
    return {"workflow_id": workflow_id, "workflow": str(result)}


@router.post("/{workflow_id}/route", response_model=RouteResponse)
async def route_envelopes(workflow_id: str, core_container: CoreContainer = Depends(get_core_container)) -> RouteResponse:
    cmd = RouteEnvelopesCommand(workflow_id=workflow_id)
    count = await core_container.app.buses.command_bus().dispatch(cmd)
    return RouteResponse(routed=count or 0)
