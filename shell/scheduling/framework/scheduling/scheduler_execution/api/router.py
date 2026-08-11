from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from shell.platform.framework.api.dependencies import get_core_container
from shell.scheduling.application.scheduling.scheduler_job.ports.scheduler_job_query_service import (
    SchedulerJobQueryService,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.controller import (
    SchedulerExecutionController,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.create_scheduler_execution_request import (
    CreateSchedulerExecutionRequest,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.create_scheduler_execution_response import (
    CreateSchedulerExecutionResponse,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.scheduler_execution_response import (
    SchedulerExecutionResponse,
)

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol

router = APIRouter(prefix="/scheduler-executions", tags=["SchedulerExecutions"])


def get_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> SchedulerExecutionController:
    command_bus = container.app.buses.command_bus if hasattr(container, "app") else container.command_bus()
    try:
        query_service: SchedulerJobQueryService = (
            container.infra.scheduler_job_query_service
            if hasattr(container, "app")
            else container.scheduler_job_query_service()
        )
    except Exception:
        raise HTTPException(
            status_code=501, detail="SchedulerExecution query service not implemented"
        ) from None
    return SchedulerExecutionController(command_bus, query_service)


@router.get("/", response_model=list[SchedulerExecutionResponse])
async def list_scheduler_executions(
    controller: SchedulerExecutionController = Depends(get_controller),
) -> list[SchedulerExecutionResponse]:
    return await controller.list_scheduler_executions()


@router.get("/{scheduler_execution_id}", response_model=SchedulerExecutionResponse)
async def get_scheduler_execution(
    scheduler_execution_id: str,
    controller: SchedulerExecutionController = Depends(get_controller),
) -> SchedulerExecutionResponse:
    return await controller.get_scheduler_execution(scheduler_execution_id)


@router.post("/", response_model=CreateSchedulerExecutionResponse, status_code=201)
async def create_scheduler_execution(
    body: CreateSchedulerExecutionRequest,
    controller: SchedulerExecutionController = Depends(get_controller),
) -> CreateSchedulerExecutionResponse:
    return await controller.create_scheduler_execution(body)


@router.put("/{scheduler_execution_id}", status_code=204)
async def update_scheduler_execution(
    scheduler_execution_id: str,
    controller: SchedulerExecutionController = Depends(get_controller),
) -> None:
    await controller.update_scheduler_execution(scheduler_execution_id)


@router.delete("/{scheduler_execution_id}", status_code=204)
async def delete_scheduler_execution(
    scheduler_execution_id: str,
    controller: SchedulerExecutionController = Depends(get_controller),
) -> None:
    await controller.delete_scheduler_execution(scheduler_execution_id)
