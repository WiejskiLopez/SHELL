from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.scheduling.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
    CreateSchedulerDefinitionCommand,
)
from shell.scheduling.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
    DeleteSchedulerDefinitionCommand,
)
from shell.scheduling.application.scheduling.scheduler_definition.commands.update_scheduler_definition_command import (
    UpdateSchedulerDefinitionCommand,
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.create_scheduler_definition_request import (
    CreateSchedulerDefinitionRequest as ApiCreateRequest,
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.create_scheduler_definition_response import (
    CreateSchedulerDefinitionResponse as ApiCreateResponse,
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.scheduler_definition_response import (
    SchedulerDefinitionResponse as ApiSchedulerDefinitionResponse,
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.update_scheduler_definition_request import (
    UpdateSchedulerDefinitionRequest as ApiUpdateRequest,
)

if TYPE_CHECKING:
    from shell.scheduling.application.scheduling.scheduler_definition.ports.scheduler_definition_query_service import (
        SchedulerDefinitionQueryService,
    )


class SchedulerDefinitionController:
    __slots__ = ("_command_bus", "_query_service")

    def __init__(
        self,
        command_bus: CommandBus,
        query_service: SchedulerDefinitionQueryService,
    ) -> None:
        self._command_bus = command_bus
        self._query_service = query_service

    async def get_scheduler_definition(
        self, scheduler_definition_id: str
    ) -> ApiSchedulerDefinitionResponse:
        result = await self._query_service.get_by_id(scheduler_definition_id)
        if result is None:
            raise HTTPException(
                status_code=404,
                detail=f"SchedulerDefinition '{scheduler_definition_id}' not found",
            )
        return ApiSchedulerDefinitionResponse(
            id=result.id,
            name=result.name,
            description=result.description,
            enabled=result.enabled,
            created_at=result.created_at,
            updated_at=result.updated_at,
        )

    async def create_scheduler_definition(self, body: ApiCreateRequest) -> ApiCreateResponse:
        definition_id = await self._command_bus.dispatch(
            CreateSchedulerDefinitionCommand(
                name=body.name,
                trigger_config=body.trigger_config,
                action_config=body.action_config,
                execution_policy=body.execution_policy,
                enabled=body.enabled,
                description=body.description,
            )
        )
        return ApiCreateResponse(id=definition_id)

    async def update_scheduler_definition(
        self, scheduler_definition_id: str, body: ApiUpdateRequest
    ) -> None:
        try:
            await self._command_bus.dispatch(
                UpdateSchedulerDefinitionCommand(scheduler_definition_id=scheduler_definition_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_scheduler_definition(self, scheduler_definition_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                DeleteSchedulerDefinitionCommand(scheduler_definition_id=scheduler_definition_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
