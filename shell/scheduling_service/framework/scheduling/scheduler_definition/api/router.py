from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import get_command_bus, get_query_bus
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.change_scheduler_definition_request import (
    ChangeSchedulerDefinitionRequest,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.controller import (
    SchedulerDefinitionController,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.create_scheduler_definition_request import (
    CreateSchedulerDefinitionRequest,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.create_scheduler_definition_response import (
    CreateSchedulerDefinitionResponse,
)
from shell.scheduling_service.framework.scheduling.scheduler_definition.api.scheduler_definition_response import (
    SchedulerDefinitionResponse,
)

router = APIRouter(prefix="/scheduler-definitions", tags=["SchedulerDefinitions"])


def get_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> SchedulerDefinitionController:
    return SchedulerDefinitionController(command_bus, query_bus)


@router.get("/{scheduler_definition_id}", response_model=SchedulerDefinitionResponse)
async def get_scheduler_definition(
    scheduler_definition_id: str,
    controller: SchedulerDefinitionController = Depends(get_controller),
) -> SchedulerDefinitionResponse:
    return await controller.get_scheduler_definition(scheduler_definition_id)


@router.post("/", response_model=CreateSchedulerDefinitionResponse, status_code=201)
async def create_scheduler_definition(
    body: CreateSchedulerDefinitionRequest,
    controller: SchedulerDefinitionController = Depends(get_controller),
) -> CreateSchedulerDefinitionResponse:
    return await controller.create_scheduler_definition(body)


@router.put("/{scheduler_definition_id}", status_code=204)
async def change_scheduler_definition(
    scheduler_definition_id: str,
    body: ChangeSchedulerDefinitionRequest,
    controller: SchedulerDefinitionController = Depends(get_controller),
) -> None:
    await controller.change_scheduler_definition(scheduler_definition_id, body)


@router.delete("/{scheduler_definition_id}", status_code=204)
async def delete_scheduler_definition(
    scheduler_definition_id: str,
    controller: SchedulerDefinitionController = Depends(get_controller),
) -> None:
    await controller.delete_scheduler_definition(scheduler_definition_id)
