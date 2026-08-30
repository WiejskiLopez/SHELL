"""Edge executions router — CRUD for edge_execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.execution_service.framework.execution.edge_execution.api.change_edge_execution_request import (
    ChangeEdgeExecutionRequest,
)
from shell.execution_service.framework.execution.edge_execution.api.controller import (
    EdgeExecutionController,
)
from shell.execution_service.framework.execution.edge_execution.api.create_edge_execution_request import (
    CreateEdgeExecutionRequest,
)
from shell.execution_service.framework.execution.edge_execution.api.edge_execution_response import (
    EdgeExecutionResponse,
)
from shell.platform.framework.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol

router = APIRouter(prefix="/edge-executions", tags=["EdgeExecutions"])


def get_edge_execution_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> EdgeExecutionController:
    command_bus = (
        container.app.buses.command_bus if hasattr(container, "app") else container.command_bus()
    )
    query_bus = (
        container.app.buses.query_bus if hasattr(container, "app") else container.query_bus()
    )
    return EdgeExecutionController(command_bus=command_bus, query_bus=query_bus)


@router.get("/{edge_execution_id}", response_model=EdgeExecutionResponse)
async def get_edge_execution(
    edge_execution_id: str,
    controller: EdgeExecutionController = Depends(get_edge_execution_controller),
) -> EdgeExecutionResponse:
    return await controller.get_edge_execution(edge_execution_id)


@router.post("", response_model=EdgeExecutionResponse, status_code=201)
async def create_edge_execution(
    body: CreateEdgeExecutionRequest,
    controller: EdgeExecutionController = Depends(get_edge_execution_controller),
) -> EdgeExecutionResponse:
    return await controller.create_edge_execution(body)


@router.put("/{edge_execution_id}", status_code=204)
async def change_edge_execution(
    edge_execution_id: str,
    body: ChangeEdgeExecutionRequest,
    controller: EdgeExecutionController = Depends(get_edge_execution_controller),
) -> None:
    return await controller.change_edge_execution(edge_execution_id, body)


@router.delete("/{edge_execution_id}", status_code=204)
async def delete_edge_execution(
    edge_execution_id: str,
    controller: EdgeExecutionController = Depends(get_edge_execution_controller),
) -> None:
    return await controller.delete_edge_execution(edge_execution_id)
