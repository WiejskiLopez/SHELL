"""Tasks router — import and query tasks."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from shell_ddd.application.commands.commands import ImportTaskCommand
from shell_ddd.application.queries.queries import GetTaskByNameQuery
from shell_ddd.bootstrap.container import Container

router = APIRouter(prefix="/tasks", tags=["tasks"])


class ImportTaskRequest(BaseModel):
    task_name: str
    md_path: str
    yaml_path: str


class ImportTaskResponse(BaseModel):
    task_id: str


def get_container(request: Request) -> Container:
    return request.app.state.container


@router.post("/import", response_model=ImportTaskResponse, status_code=201)
async def import_task(body: ImportTaskRequest, container: Container = Depends(get_container)) -> ImportTaskResponse:
    cmd = ImportTaskCommand(md_path=body.md_path, task_name=body.task_name)
    task_id = await container.command_bus.dispatch(cmd)
    return ImportTaskResponse(task_id=str(task_id))


@router.get("/{name}")
async def get_task(name: str, container: Container = Depends(get_container)) -> dict:  # type: ignore[type-arg]
    result = await container.query_bus.dispatch(GetTaskByNameQuery(name=name))
    if result is None:
        raise HTTPException(status_code=404, detail=f"Task '{name}' not found")
    return {"name": name, "task": str(result)}
