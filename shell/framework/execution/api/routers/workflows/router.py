"""Workflows router — start and query workflows."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.application.platform.bus.command_bus import (
    CommandBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.application.platform.bus.query_bus import (
    QueryBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.framework.execution.api.routers.workflows.controller import WorkflowController
from shell.framework.execution.api.routers.workflows.start_workflow_request import (
    StartWorkflowRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.framework.execution.api.routers.workflows.start_workflow_response import (
    StartWorkflowResponse,
)
from shell.framework.platform.api.dependencies import get_command_bus, get_query_bus

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> WorkflowController:
    return WorkflowController(command_bus=command_bus, query_bus=query_bus)


@router.post("", response_model=StartWorkflowResponse, status_code=201)
async def start_workflow(
    start_workflow_request: StartWorkflowRequest,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> StartWorkflowResponse:
    return await controller.start_workflow(start_workflow_request.task_execution_id)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> dict:
    return await controller.get_workflow(workflow_id)
