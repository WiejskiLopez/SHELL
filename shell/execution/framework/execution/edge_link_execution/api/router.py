"""Edge link executions router — CRUD for edge_link_execution."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from shell.execution.framework.execution.edge_link_execution.api.controller import (
    EdgeLinkExecutionController,
)
from shell.execution.framework.execution.edge_link_execution.api.create_edge_link_execution_request import (
    CreateEdgeLinkExecutionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.execution.framework.execution.edge_link_execution.api.edge_link_execution_response import (
    EdgeLinkExecutionResponse,
)
from shell.platform.framework.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol

router = APIRouter(prefix="/edge-links", tags=["EdgeLinkExecutions"])


def get_edge_link_execution_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> EdgeLinkExecutionController:
    command_bus = (
        container.app.buses.command_bus if hasattr(container, "app") else container.command_bus()
    )
    query_bus = (
        container.app.buses.query_bus if hasattr(container, "app") else container.query_bus()
    )
    return EdgeLinkExecutionController(command_bus=command_bus, query_bus=query_bus)


@router.get("/{link_id}", response_model=EdgeLinkExecutionResponse)
async def get_edge_link_execution(
    link_id: str,
    controller: EdgeLinkExecutionController = Depends(get_edge_link_execution_controller),
) -> EdgeLinkExecutionResponse:
    return await controller.get_edge_link_execution(link_id)


@router.post("", response_model=EdgeLinkExecutionResponse, status_code=201)
async def create_edge_link_execution(
    body: CreateEdgeLinkExecutionRequest,
    controller: EdgeLinkExecutionController = Depends(get_edge_link_execution_controller),
) -> EdgeLinkExecutionResponse:
    return await controller.create_edge_link_execution(body)


@router.delete("/{link_id}", status_code=204)
async def delete_edge_link_execution(
    link_id: str,
    controller: EdgeLinkExecutionController = Depends(get_edge_link_execution_controller),
) -> None:
    return await controller.delete_edge_link_execution(link_id)
