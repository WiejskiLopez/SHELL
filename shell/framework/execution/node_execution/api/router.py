"""Nodes router — query node execution results."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.framework.execution.node_execution.api.controller import (
    NodeExecutionController,
)
from shell.framework.execution.node_execution.api.create_node_execution_request import (
    CreateNodeExecutionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.framework.execution.node_execution.api.create_node_execution_response import (
    CreateNodeExecutionResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.framework.execution.node_execution.api.node_execution_response import (
    NodeExecutionResponse,
)
from shell.framework.execution.node_execution.api.node_execution_result_response import (
    NodeExecutionResultResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container

router = APIRouter(prefix="/node-executions", tags=["NodeExecutions"])


def get_node_execution_controller(
    container: CoreContainer = Depends(get_core_container),
) -> NodeExecutionController:
    command_bus = container.app.buses.command_bus
    query_bus = container.app.buses.query_bus
    return NodeExecutionController(command_bus=command_bus, query_bus=query_bus)


@router.get("/{node_execution_id}", response_model=NodeExecutionResponse)
async def get_node_execution(
    node_execution_id: str,
    controller: NodeExecutionController = Depends(get_node_execution_controller),
) -> NodeExecutionResponse:
    return await controller.get_node_execution(node_execution_id)


@router.get("/{node_execution_id}/result")
async def get_node_execution_result(
    node_execution_id: str,
    workflow_id: str,
    controller: NodeExecutionController = Depends(get_node_execution_controller),
) -> NodeExecutionResultResponse:
    return await controller.get_node_execution_result(
        node_execution_id=node_execution_id, workflow_id=workflow_id
    )


@router.post("/", response_model=CreateNodeExecutionResponse, status_code=201)
async def create_node_execution(
    body: CreateNodeExecutionRequest,
    controller: NodeExecutionController = Depends(get_node_execution_controller),
) -> CreateNodeExecutionResponse:
    return await controller.create_node_execution(body)


@router.delete("/{node_execution_id}", status_code=204)
async def delete_node_execution(
    node_execution_id: str,
    controller: NodeExecutionController = Depends(get_node_execution_controller),
) -> None:
    await controller.delete_node_execution(node_execution_id)
