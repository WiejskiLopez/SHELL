"""Task executions router — query task executions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException, Query

from shell.framework.execution.task_execution.api.controller import TaskExecutionController
from shell.framework.execution.task_execution.api.task_execution_response import (
    TaskExecutionResponse,
)
from shell.platform.framework.api.dependencies import get_core_container
from shell.platform.framework.api.models.page import Page

if TYPE_CHECKING:
    from shell.platform.application.bus.query_bus import QueryBus
    from shell.platform.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/task-executions", tags=["Task Executions"])


def get_task_execution_controller(
    container: CoreContainer = Depends(get_core_container),
) -> TaskExecutionController:
    try:
        query_bus: QueryBus = container.app.buses.query_bus
    except Exception:
        raise HTTPException(
            status_code=501, detail="Task execution query service not implemented"
        ) from None
    return TaskExecutionController(query_bus)


@router.get("", response_model=Page[TaskExecutionResponse])
async def list_task_executions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000, alias="page_size"),
    controller: TaskExecutionController = Depends(get_task_execution_controller),
) -> Page[TaskExecutionResponse]:
    return await controller.list_task_executions(page=page, page_size=page_size)
