from __future__ import annotations

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.scheduling_service.application.scheduling.scheduler_job.commands.change_scheduler_job_command import (
    ChangeSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.create_scheduler_job_command import (
    CreateSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.commands.delete_scheduler_job_command import (
    DeleteSchedulerJobCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_job.exceptions.scheduler_job_not_found_error import (
    SchedulerJobNotFoundError,
)
from shell.scheduling_service.application.scheduling.scheduler_job.queries.get_scheduler_job_by_id_query import (
    GetSchedulerJobByIdQuery,
)
from shell.scheduling_service.application.scheduling.scheduler_job.queries.list_scheduler_jobs_query import (
    ListSchedulerJobsQuery,
)
from shell.scheduling_service.framework.scheduling.scheduler_job.api.create_scheduler_job_request import (
    CreateSchedulerJobRequest as ApiCreateRequest,
)
from shell.scheduling_service.framework.scheduling.scheduler_job.api.create_scheduler_job_response import (
    CreateSchedulerJobResponse as ApiCreateResponse,
)
from shell.scheduling_service.framework.scheduling.scheduler_job.api.scheduler_job_response import (
    SchedulerJobResponse as ApiSchedulerJobResponse,
)


class SchedulerJobController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
    ) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_scheduler_job(self, scheduler_job_id: str) -> ApiSchedulerJobResponse:
        result = await self._query_bus.dispatch(
            GetSchedulerJobByIdQuery(scheduler_job_id=scheduler_job_id)
        )
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
            changed_at=result.changed_at,
        )

    async def list_scheduler_jobs(
        self,
    ) -> list[ApiSchedulerJobResponse]:
        result = await self._query_bus.dispatch(ListSchedulerJobsQuery())
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
                changed_at=d.changed_at,
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

    async def change_scheduler_job(self, scheduler_job_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                ChangeSchedulerJobCommand(scheduler_job_id=scheduler_job_id)
            )
        except SchedulerJobNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def delete_scheduler_job(self, scheduler_job_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                DeleteSchedulerJobCommand(scheduler_job_id=scheduler_job_id)
            )
        except SchedulerJobNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
