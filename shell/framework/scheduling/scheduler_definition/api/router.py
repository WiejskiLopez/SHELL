from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell.application.scheduling.scheduler_definition.ports.scheduler_definition_query_service import (
    SchedulerDefinitionQueryService,
)
from shell.framework.scheduling.scheduler_definition.api.controller import (
    SchedulerDefinitionController,
)
from shell.framework.scheduling.scheduler_definition.api.create_scheduler_definition_request import (
    CreateSchedulerDefinitionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.framework.scheduling.scheduler_definition.api.create_scheduler_definition_response import (
    CreateSchedulerDefinitionResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.framework.scheduling.scheduler_definition.api.scheduler_definition_response import (
    SchedulerDefinitionResponse,
)
from shell.framework.scheduling.scheduler_definition.api.update_scheduler_definition_request import (
    UpdateSchedulerDefinitionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.platform.application.bus.command_bus import (
    CommandBus,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container

router = APIRouter(prefix="/scheduler-definitions", tags=["SchedulerDefinitions"])


def get_controller(
    container: CoreContainer = Depends(get_core_container),
) -> SchedulerDefinitionController:
    command_bus: CommandBus = container.app.buses.command_bus
    try:
        query_service: SchedulerDefinitionQueryService = (
            container.infra.scheduler_definition_query_service
        )
    except Exception:
        raise HTTPException(
            status_code=501, detail="SchedulerDefinition query service not implemented"
        ) from None
    return SchedulerDefinitionController(command_bus, query_service)


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
async def update_scheduler_definition(
    scheduler_definition_id: str,
    body: UpdateSchedulerDefinitionRequest,
    controller: SchedulerDefinitionController = Depends(get_controller),
) -> None:
    await controller.update_scheduler_definition(scheduler_definition_id, body)


@router.delete("/{scheduler_definition_id}", status_code=204)
async def delete_scheduler_definition(
    scheduler_definition_id: str,
    controller: SchedulerDefinitionController = Depends(get_controller),
) -> None:
    await controller.delete_scheduler_definition(scheduler_definition_id)
