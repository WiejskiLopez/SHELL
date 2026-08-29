from __future__ import annotations

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.change_scheduler_definition_command import (
    ChangeSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.create_scheduler_definition_command import (
    CreateSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.commands.delete_scheduler_definition_command import (
    DeleteSchedulerDefinitionCommand,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.exceptions.scheduler_definition_not_found_error import (
    SchedulerDefinitionNotFoundError,
)
from shell.scheduling_service.application.scheduling.scheduler_definition.queries.get_scheduler_definition_by_id_query import (
    GetSchedulerDefinitionByIdQuery,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.change_scheduler_definition_request import (
    ChangeSchedulerDefinitionRequest as ApiChangeRequest,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.create_scheduler_definition_request import (
    CreateSchedulerDefinitionRequest as ApiCreateRequest,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.create_scheduler_definition_response import (
    CreateSchedulerDefinitionResponse as ApiCreateResponse,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.scheduler_definition_response import (
    SchedulerDefinitionResponse as ApiSchedulerDefinitionResponse,
)


class SchedulerDefinitionController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
    ) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_scheduler_definition(
        self, scheduler_definition_id: str
    ) -> ApiSchedulerDefinitionResponse:
        result = await self._query_bus.dispatch(
            GetSchedulerDefinitionByIdQuery(scheduler_definition_id=scheduler_definition_id)
        )
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
            changed_at=result.changed_at,
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

    async def change_scheduler_definition(
        self, scheduler_definition_id: str, body: ApiChangeRequest
    ) -> None:
        try:
            await self._command_bus.dispatch(
                ChangeSchedulerDefinitionCommand(scheduler_definition_id=scheduler_definition_id)
            )
        except SchedulerDefinitionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    async def delete_scheduler_definition(self, scheduler_definition_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                DeleteSchedulerDefinitionCommand(scheduler_definition_id=scheduler_definition_id)
            )
        except SchedulerDefinitionNotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
