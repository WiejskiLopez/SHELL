from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.scheduling.application.scheduling.scheduler_job.commands.create_scheduler_job_command import (
    CreateSchedulerJobCommand,
)
from shell.scheduling.application.scheduling.scheduler_job.commands.delete_scheduler_job_command import (
    DeleteSchedulerJobCommand,
)
from shell.scheduling.application.scheduling.scheduler_job.commands.update_scheduler_job_command import (
    UpdateSchedulerJobCommand,
)
from shell.scheduling.framework.scheduling.scheduler_job.api.create_scheduler_job_request import (
    CreateSchedulerJobRequest as ApiCreateRequest,
)
from shell.scheduling.framework.scheduling.scheduler_job.api.create_scheduler_job_response import (
    CreateSchedulerJobResponse as ApiCreateResponse,
)
from shell.scheduling.framework.scheduling.scheduler_job.api.scheduler_job_response import (
    SchedulerJobResponse as ApiSchedulerJobResponse,
)

if TYPE_CHECKING:
    from shell.scheduling.application.scheduling.scheduler_execution.ports.scheduler_execution_query_service import (
        SchedulerExecutionQueryService,
    )


class SchedulerJobController:
    __slots__ = ("_command_bus", "_query_service")

    def __init__(
        self,
        command_bus: CommandBus,
        query_service: SchedulerExecutionQueryService,
    ) -> None:
        self._command_bus = command_bus
        self._query_service = query_service

    async def get_scheduler_job(self, scheduler_job_id: str) -> ApiSchedulerJobResponse:
        result = await self._query_service.get_by_id(scheduler_job_id)
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"SchedulerJob '{scheduler_job_id}' not found"
            )
        return ApiSchedulerJobResponse(
            id=result.id,
            scheduler_definition_id=result.scheduler_definition_id,
            name=result.name,
            job_type=result.job_type,
            interval_seconds=result.interval_seconds,
            batch_size=result.batch_size,
            enabled=result.enabled,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    async def list_scheduler_jobs(
        self,
    ) -> list[ApiSchedulerJobResponse]:
        result = await self._query_service.list_all()
        if result is None:
            return []
        dtos, _ = result
        return [
            ApiSchedulerJobResponse(
                id=d.id,
                scheduler_definition_id=d.scheduler_definition_id,
                name=d.name,
                job_type=d.job_type,
                interval_seconds=d.interval_seconds,
                batch_size=d.batch_size,
                enabled=d.enabled,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in dtos
        ]

    async def create_scheduler_job(self, body: ApiCreateRequest) -> ApiCreateResponse:
        job_id = await self._command_bus.dispatch(
            CreateSchedulerJobCommand(
                scheduler_definition_id=body.scheduler_definition_id,
                name=body.name,
                job_type=body.job_type,
                interval_seconds=body.interval_seconds,
                batch_size=body.batch_size,
                enabled=body.enabled,
            )
        )
        return ApiCreateResponse(id=job_id)

    async def update_scheduler_job(self, scheduler_job_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                UpdateSchedulerJobCommand(scheduler_job_id=scheduler_job_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_scheduler_job(self, scheduler_job_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                DeleteSchedulerJobCommand(scheduler_job_id=scheduler_job_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
