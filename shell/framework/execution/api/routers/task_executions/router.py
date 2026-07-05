"""task_executions router — import and query task_executions."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.application.platform.bus.command_bus import (
    CommandBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.application.platform.bus.query_bus import (
    QueryBus,  # noqa: TC001 — FastAPI wymaga runtime do Dependency Injection
)
from shell.framework.execution.api.routers.task_executions.controller import TaskExecutionController
from shell.framework.execution.api.routers.task_executions.import_task_request import (
    ImportTaskRequest,  # noqa: TC001 — Pydantic model wymagany przez FastAPI w runtime
)
from shell.framework.execution.api.routers.task_executions.import_task_response import (
    ImportTaskResponse,
)
from shell.framework.platform.api.dependencies import get_command_bus, get_query_bus

router = APIRouter(prefix="/task_executions", tags=["task_executions"])


def get_task_execution_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> TaskExecutionController:
    return TaskExecutionController(command_bus=command_bus, query_bus=query_bus)


@router.post("/import", response_model=ImportTaskResponse, status_code=201)
async def import_task(
    body: ImportTaskRequest,
    controller: TaskExecutionController = Depends(get_task_execution_controller),
) -> ImportTaskResponse:
    return await controller.import_task(md_path=body.md_path, task_execution_name=body.task_execution_name)


@router.get("/{name}")
async def get_task(
    name: str,
    controller: TaskExecutionController = Depends(get_task_execution_controller),
) -> dict:
    return await controller.get_task(name)
