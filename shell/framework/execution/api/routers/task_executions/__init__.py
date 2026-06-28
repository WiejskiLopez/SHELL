"""task_executions router — import and query task_executions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request
from shell.application.platform.commands import ImportTaskExecutionCommand
from shell.application.platform.queries.queries import TaskExecutionGetByNameQuery
from shell.framework.execution.api.routers.task_executions.import_task_request import (
    ImportTaskRequest,  # noqa: TC002 — ImportTaskRequest używany w parametrach endpointów FastAPI
)
from shell.framework.execution.api.routers.task_executions.import_task_response import (
    ImportTaskResponse,
)

if TYPE_CHECKING:
    from shell.application.platform.bus.command_bus import CommandBus
    from shell.application.platform.bus.query_bus import QueryBus
    from shell.bootstrap.platform.container.core_container import CoreContainer

router = APIRouter(prefix="/task_executions", tags=["task_executions"])


def get_core_container(request: Request) -> CoreContainer:
    return request.app.state.core_container


def get_command_bus(container: CoreContainer = Depends(get_core_container)) -> CommandBus:
    return container.app.buses.command_bus()  # type: ignore[attr-defined]


def get_query_bus(container: CoreContainer = Depends(get_core_container)) -> QueryBus:
    return container.app.buses.query_bus()  # type: ignore[attr-defined]


@router.post("/import", response_model=ImportTaskResponse, status_code=201)
async def import_task(
    body: ImportTaskRequest,
    command_bus: CommandBus = Depends(get_command_bus),
) -> ImportTaskResponse:
    command = ImportTaskExecutionCommand(
        md_path=body.md_path, task_execution_name=body.task_execution_name
    )
    task_execution_id = await command_bus.dispatch(command)
    return ImportTaskResponse(task_execution_id=str(task_execution_id))


@router.get("/{name}")
async def get_task(
    name: str,
    query_bus: QueryBus = Depends(get_query_bus),
) -> dict:
    result = await query_bus.dispatch(TaskExecutionGetByNameQuery(name=name))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task '{name}' not found")
    return {"name": name, "task": str(result)}
