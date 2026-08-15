from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import get_command_bus, get_query_bus
from shell.scheduling_service.framework.scheduling.scheduler_job.api.controller import (
    SchedulerJobController,
)
from shell.scheduling_service.framework.scheduling.scheduler_job.api.create_scheduler_job_request import (
    CreateSchedulerJobRequest,
)
from shell.scheduling_service.framework.scheduling.scheduler_job.api.create_scheduler_job_response import (
    CreateSchedulerJobResponse,
)
from shell.scheduling_service.framework.scheduling.scheduler_job.api.scheduler_job_response import (
    SchedulerJobResponse,
)

router = APIRouter(prefix="/scheduler-jobs", tags=["SchedulerJobs"])


def get_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> SchedulerJobController:
    return SchedulerJobController(command_bus, query_bus)


@router.get("/", response_model=list[SchedulerJobResponse])
async def list_scheduler_jobs(
    controller: SchedulerJobController = Depends(get_controller),
) -> list[SchedulerJobResponse]:
    return await controller.list_scheduler_jobs()


@router.get("/{scheduler_job_id}", response_model=SchedulerJobResponse)
async def get_scheduler_job(
    scheduler_job_id: str,
    controller: SchedulerJobController = Depends(get_controller),
) -> SchedulerJobResponse:
    return await controller.get_scheduler_job(scheduler_job_id)


@router.post("/", response_model=CreateSchedulerJobResponse, status_code=201)
async def create_scheduler_job(
    body: CreateSchedulerJobRequest,
    controller: SchedulerJobController = Depends(get_controller),
) -> CreateSchedulerJobResponse:
    return await controller.create_scheduler_job(body)


@router.put("/{scheduler_job_id}", status_code=204)
async def change_scheduler_job(
    scheduler_job_id: str,
    controller: SchedulerJobController = Depends(get_controller),
) -> None:
    await controller.change_scheduler_job(scheduler_job_id)


@router.delete("/{scheduler_job_id}", status_code=204)
async def delete_scheduler_job(
    scheduler_job_id: str,
    controller: SchedulerJobController = Depends(get_controller),
) -> None:
    await controller.delete_scheduler_job(scheduler_job_id)
