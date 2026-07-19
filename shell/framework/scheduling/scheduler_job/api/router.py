from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell.application.scheduling.scheduler_execution.ports.scheduler_execution_query_service import (
    SchedulerExecutionQueryService,
)
from shell.framework.scheduling.scheduler_job.api.controller import SchedulerJobController
from shell.framework.scheduling.scheduler_job.api.create_scheduler_job_request import (
    CreateSchedulerJobRequest,
)
from shell.framework.scheduling.scheduler_job.api.create_scheduler_job_response import (
    CreateSchedulerJobResponse,
)
from shell.framework.scheduling.scheduler_job.api.scheduler_job_response import SchedulerJobResponse
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container

router = APIRouter(prefix="/scheduler-jobs", tags=["SchedulerJobs"])


def get_controller(
    container: CoreContainer = Depends(get_core_container),
) -> SchedulerJobController:
    command_bus: CommandBus = container.app.buses.command_bus
    try:
        query_service: SchedulerExecutionQueryService = (
            container.infra.scheduler_execution_query_service
        )
    except Exception:
        raise HTTPException(
            status_code=501, detail="SchedulerJob query service not implemented"
        ) from None
    return SchedulerJobController(command_bus, query_service)


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
async def update_scheduler_job(
    scheduler_job_id: str,
    controller: SchedulerJobController = Depends(get_controller),
) -> None:
    await controller.update_scheduler_job(scheduler_job_id)


@router.delete("/{scheduler_job_id}", status_code=204)
async def delete_scheduler_job(
    scheduler_job_id: str,
    controller: SchedulerJobController = Depends(get_controller),
) -> None:
    await controller.delete_scheduler_job(scheduler_job_id)
