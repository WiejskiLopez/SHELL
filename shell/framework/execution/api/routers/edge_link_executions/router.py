"""Edge link executions router — CRUD for edge_link_execution."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.application.platform.bus.command_bus import (
    CommandBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.framework.execution.api.routers.edge_link_executions.controller import (
    EdgeLinkExecutionController,
)
from shell.framework.execution.api.routers.edge_link_executions.create_edge_link_execution_request import (
    CreateEdgeLinkExecutionRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.framework.execution.api.routers.edge_link_executions.edge_link_execution_response import (
    EdgeLinkExecutionResponse,
)
from shell.framework.platform.api.dependencies import get_command_bus

router = APIRouter(prefix="/edge-links", tags=["edge-links"])


def get_edge_link_execution_controller(
    command_bus: CommandBus = Depends(get_command_bus),
) -> EdgeLinkExecutionController:
    return EdgeLinkExecutionController(command_bus=command_bus)


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
