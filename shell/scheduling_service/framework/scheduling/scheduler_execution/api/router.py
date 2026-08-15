from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import get_command_bus, get_query_bus
from shell.scheduling_service.framework.scheduling.scheduler_execution.api.controller import (
    SchedulerExecutionController,
)
from shell.scheduling_service.framework.scheduling.scheduler_execution.api.create_scheduler_execution_request import (
    CreateSchedulerExecutionRequest,
)
from shell.scheduling_service.framework.scheduling.scheduler_execution.api.create_scheduler_execution_response import (
    CreateSchedulerExecutionResponse,
)
from shell.scheduling_service.framework.scheduling.scheduler_execution.api.scheduler_execution_response import (
    SchedulerExecutionResponse,
)

router = APIRouter(prefix="/scheduler-executions", tags=["SchedulerExecutions"])


def get_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> SchedulerExecutionController:
    return SchedulerExecutionController(command_bus, query_bus)


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
