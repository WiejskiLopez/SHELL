"""Nodes router — query node execution results."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.framework.execution.node_execution.api.controller import (
    NodeExecutionController,
)
from shell.framework.execution.node_execution.api.node_execution_result_response import (
    NodeExecutionResultResponse,  # noqa: TC001 — FastAPI needs it at runtime for response_model
)
from shell.platform.framework.api.dependencies import get_query_bus

if TYPE_CHECKING:
    from shell.platform.application.bus.query_bus import QueryBus

router = APIRouter(prefix="/node-executions", tags=["node-executions"])


def get_node_execution_controller(
    query_bus: QueryBus = Depends(get_query_bus),
) -> NodeExecutionController:
    return NodeExecutionController(query_bus=query_bus)


@router.get("/{node_execution_id}/result")
async def get_node_execution_result(
    node_execution_id: str,
    workflow_id: str,
    controller: NodeExecutionController = Depends(get_node_execution_controller),
) -> NodeExecutionResultResponse:
    return await controller.get_node_execution_result(
        node_execution_id=node_execution_id, workflow_id=workflow_id
    )
