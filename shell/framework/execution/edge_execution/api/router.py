"""Edge executions router — CRUD for edge_execution."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.application.platform.bus.command_bus import (
    CommandBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.framework.execution.edge_execution.api.controller import (
    EdgeExecutionController,
)
from shell.framework.execution.edge_execution.api.create_edge_execution_request import (
    CreateEdgeExecutionRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.framework.execution.edge_execution.api.edge_execution_response import (
    EdgeExecutionResponse,
)
from shell.framework.execution.edge_execution.api.update_edge_execution_request import (
    UpdateEdgeExecutionRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.framework.platform.api.dependencies import get_command_bus

router = APIRouter(prefix="/edges", tags=["edges"])


def get_edge_execution_controller(
    command_bus: CommandBus = Depends(get_command_bus),
) -> EdgeExecutionController:
    return EdgeExecutionController(command_bus=command_bus)


@router.post("", response_model=EdgeExecutionResponse, status_code=201)
async def create_edge_execution(
    body: CreateEdgeExecutionRequest,
    controller: EdgeExecutionController = Depends(get_edge_execution_controller),
) -> EdgeExecutionResponse:
    return await controller.create_edge_execution(body)


@router.put("/{edge_execution_id}", status_code=200)
async def update_edge_execution(
    edge_execution_id: str,
    body: UpdateEdgeExecutionRequest,
    controller: EdgeExecutionController = Depends(get_edge_execution_controller),
) -> None:
    return await controller.update_edge_execution(edge_execution_id, body)


@router.delete("/{edge_execution_id}", status_code=204)
async def delete_edge_execution(
    edge_execution_id: str,
    controller: EdgeExecutionController = Depends(get_edge_execution_controller),
) -> None:
    return await controller.delete_edge_execution(edge_execution_id)
