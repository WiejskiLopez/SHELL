"""Workflows router — query workflows."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from shell.execution_service.framework.execution.workflow.api.change_workflow_request import (
    ChangeWorkflowRequest,
)
from shell.execution_service.framework.execution.workflow.api.controller import WorkflowController
from shell.execution_service.framework.execution.workflow.api.create_workflow_request import (
    CreateWorkflowRequest,
)
from shell.execution_service.framework.execution.workflow.api.create_workflow_response import (
    CreateWorkflowResponse,
)
from shell.execution_service.framework.execution.workflow.api.workflow_response import (
    WorkflowResponse,
)
from shell.platform.framework.api.dependencies import ContainerProtocol, get_core_container
from shell.platform.framework.api.models.page import Page

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def get_workflow_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> WorkflowController:
    command_bus = (
        container.app.buses.command_bus if hasattr(container, "app") else container.command_bus()
    )
    query_bus = (
        container.app.buses.query_bus if hasattr(container, "app") else container.query_bus()
    )
    return WorkflowController(command_bus, query_bus)


@router.get("", response_model=Page[WorkflowResponse])
async def list_workflows(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000, alias="page_size"),
    status: str | None = Query(default=None),
    controller: WorkflowController = Depends(get_workflow_controller),
) -> Page[WorkflowResponse]:
    return await controller.list_workflows(page=page, page_size=page_size, status=status)


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> WorkflowResponse:
    return await controller.get_workflow(workflow_id)


@router.post("/", response_model=CreateWorkflowResponse, status_code=201)
async def create_workflow(
    body: CreateWorkflowRequest,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> CreateWorkflowResponse:
    return await controller.create_workflow(body)


@router.put("/{workflow_id}", status_code=204)
async def change_workflow(
    workflow_id: str,
    body: ChangeWorkflowRequest,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> None:
    await controller.change_workflow(workflow_id, body)


@router.delete("/{workflow_id}", status_code=204)
async def delete_workflow(
    workflow_id: str,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> None:
    await controller.delete_workflow(workflow_id)
