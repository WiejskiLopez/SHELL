"""Tasks router — import and query tasks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from shell.application.commands.commands import ImportTaskCommand
from shell.application.queries.queries import GetTaskByNameQuery

if TYPE_CHECKING:
    from shell.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ImportTaskRequest(BaseModel):
    task_name: str
    md_path: str


class ImportTaskResponse(BaseModel):
    task_id: str


def get_core_container(request: Request) -> CoreContainer:
    return request.app.state.core_container


@router.post("/import", response_model=ImportTaskResponse, status_code=201)
async def import_task(
    body: ImportTaskRequest, core_container: CoreContainer = Depends(get_core_container)
) -> ImportTaskResponse:
    cmd = ImportTaskCommand(md_path=body.md_path, task_name=body.task_name)
    task_id = await core_container.app.buses.command_bus().dispatch(cmd)
    return ImportTaskResponse(task_id=str(task_id))


@router.get("/{name}")
async def get_task(name: str, core_container: CoreContainer = Depends(get_core_container)) -> dict:  # type: ignore[type-arg]
    result = await core_container.app.buses.query_bus().dispatch(GetTaskByNameQuery(name=name))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task '{name}' not found")
    return {"name": name, "task": str(result)}
