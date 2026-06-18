"""task_executions router — import and query task_executions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from shell.application.commands.commands import ImportTaskExecutionCommand
from shell.application.queries.queries import GetTaskExecutionByNameQuery

if TYPE_CHECKING:
    from shell.application.bus.command_bus import CommandBus
    from shell.application.bus.query_bus import QueryBus
    from shell.bootstrap.container.core_container import CoreContainer
    # Dopasuj ścieżki importu szyn do swojej struktury projektu:

router = APIRouter(prefix="/task_executions", tags=["task_executions"])


class ImportTaskRequest(BaseModel):
    task_execution_name: str
    md_path: str


class ImportTaskResponse(BaseModel):
    task_execution_id: str


# ------------------------------------------------------------------
# FastAPI Dependencies (Inversion of Control)
# ------------------------------------------------------------------


def get_core_container(request: Request) -> CoreContainer:
    return request.app.state.core_container


def get_command_bus(container: CoreContainer = Depends(get_core_container)) -> CommandBus:
    """Ekstrahuje CommandBus i ucisza mypy w jednym kontrolowanym miejscu."""
    return container.app.buses.command_bus()  # type: ignore[attr-defined, no-any-return]


def get_query_bus(container: CoreContainer = Depends(get_core_container)) -> QueryBus:
    """Ekstrahuje QueryBus i ucisza mypy w jednym kontrolowanym miejscu."""
    return container.app.buses.query_bus()  # type: ignore[attr-defined, no-any-return]


# ------------------------------------------------------------------
# Endpoints
# ------------------------------------------------------------------


@router.post("/import", response_model=ImportTaskResponse, status_code=201)
async def import_task(
    body: ImportTaskRequest,
    command_bus: CommandBus = Depends(get_command_bus),  # Wstrzyknięty konkret
) -> ImportTaskResponse:
    cmd = ImportTaskExecutionCommand(
        md_path=body.md_path, task_execution_name=body.task_execution_name
    )
    task_execution_id = await command_bus.dispatch(cmd)
    return ImportTaskResponse(task_execution_id=str(task_execution_id))


@router.get("/{name}")
async def get_task(
    name: str,
    query_bus: QueryBus = Depends(get_query_bus),  # Wstrzyknięty konkret
) -> dict:  # type: ignore[type-arg]
    result = await query_bus.dispatch(GetTaskExecutionByNameQuery(name=name))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task '{name}' not found")
    return {"name": name, "task": str(result)}
