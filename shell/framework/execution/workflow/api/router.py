"""Workflows router — query workflows."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.framework.execution.workflow.api.controller import WorkflowController
from shell.framework.execution.workflow.api.workflow_response import (
    WorkflowResponse,  # noqa: TC001 — FastAPI needs it at runtime for response_model
)
from shell.platform.application.bus.query_bus import (
    QueryBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.platform.framework.api.dependencies import get_query_bus

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def get_workflow_controller(
    query_bus: QueryBus = Depends(get_query_bus),
) -> WorkflowController:
    return WorkflowController(query_bus=query_bus)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> WorkflowResponse:
    return await controller.get_workflow(workflow_id)
