from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.scheduling.application.scheduling.scheduler_execution.commands.create_scheduler_execution_command import (
    CreateSchedulerExecutionCommand,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.delete_scheduler_execution_command import (
    DeleteSchedulerExecutionCommand,
)
from shell.scheduling.application.scheduling.scheduler_execution.commands.update_scheduler_execution_command import (
    UpdateSchedulerExecutionCommand,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.create_scheduler_execution_request import (
    CreateSchedulerExecutionRequest as ApiCreateRequest,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.create_scheduler_execution_response import (
    CreateSchedulerExecutionResponse as ApiCreateResponse,
)
from shell.scheduling.framework.scheduling.scheduler_execution.api.scheduler_execution_response import (
    SchedulerExecutionResponse as ApiSchedulerExecutionResponse,
)

if TYPE_CHECKING:
    from shell.scheduling.application.scheduling.scheduler_job.ports.scheduler_job_query_service import (
        SchedulerJobQueryService,
    )


class SchedulerExecutionController:
    __slots__ = ("_command_bus", "_query_service")

    def __init__(
        self,
        command_bus: CommandBus,
        query_service: SchedulerJobQueryService,
    ) -> None:
        self._command_bus = command_bus
        self._query_service = query_service

    async def get_scheduler_execution(
        self, scheduler_execution_id: str
    ) -> ApiSchedulerExecutionResponse:
        result = await self._query_service.get_by_id(scheduler_execution_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"SchedulerExecution '{scheduler_execution_id}' not found",
            )
        return ApiSchedulerExecutionResponse(
            id=result.id,
            scheduler_definition_id=result.scheduler_definition_id,
            status=result.status,
            trigger_event_id=result.trigger_event_id,
            trigger_event_type=result.trigger_event_type,
            action_ref=result.action_ref,
            action_ref_type=result.action_ref_type,
            error=result.error,
            started_at=result.started_at,
            completed_at=result.completed_at,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    async def list_scheduler_executions(
        self,
    ) -> list[ApiSchedulerExecutionResponse]:
        result = await self._query_service.list_all()
        if result is None:
            return []
        dtos, _ = result
        return [
            ApiSchedulerExecutionResponse(
                id=d.id,
                scheduler_definition_id=d.scheduler_definition_id,
                status=d.status,
                trigger_event_id=d.trigger_event_id,
                trigger_event_type=d.trigger_event_type,
                action_ref=d.action_ref,
                action_ref_type=d.action_ref_type,
                error=d.error,
                started_at=d.started_at,
                completed_at=d.completed_at,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in dtos
        ]

    async def create_scheduler_execution(self, body: ApiCreateRequest) -> ApiCreateResponse:
        execution_id = await self._command_bus.dispatch(
            CreateSchedulerExecutionCommand(
                scheduler_definition_id=body.scheduler_definition_id,
            )
        )
        return ApiCreateResponse(id=execution_id)

    async def update_scheduler_execution(self, scheduler_execution_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                UpdateSchedulerExecutionCommand(scheduler_execution_id=scheduler_execution_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_scheduler_execution(self, scheduler_execution_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                DeleteSchedulerExecutionCommand(scheduler_execution_id=scheduler_execution_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
