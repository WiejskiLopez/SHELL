"""Workflows router — query workflows."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.application.platform.bus.query_bus import (
    QueryBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.framework.execution.workflow.api.controller import WorkflowController
from shell.framework.platform.api.dependencies import get_query_bus

router = APIRouter(prefix="/workflows", tags=["workflows"])


def get_workflow_controller(
    query_bus: QueryBus = Depends(get_query_bus),
) -> WorkflowController:
    return WorkflowController(query_bus=query_bus)


@router.get("/{workflow_id}")
async def get_workflow(
    workflow_id: str,
    controller: WorkflowController = Depends(get_workflow_controller),
) -> dict:
    return await controller.get_workflow(workflow_id)
