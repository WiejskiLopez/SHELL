from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from shell.platform.framework.api.dependencies import get_core_container
from shell.scheduling.application.scheduling.scheduler_definition.ports.scheduler_definition_query_service import (
    SchedulerDefinitionQueryService,
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.controller import (
    SchedulerDefinitionController,
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.create_scheduler_definition_request import (
    CreateSchedulerDefinitionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.create_scheduler_definition_response import (
    CreateSchedulerDefinitionResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.scheduler_definition_response import (
    SchedulerDefinitionResponse,
)
from shell.scheduling.framework.scheduling.scheduler_definition.api.update_scheduler_definition_request import (
    UpdateSchedulerDefinitionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)

if TYPE_CHECKING:
    from shell.platform.framework.api.dependencies import ContainerProtocol

router = APIRouter(prefix="/scheduler-definitions", tags=["SchedulerDefinitions"])


def get_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> SchedulerDefinitionController:
    command_bus = (
        container.app.buses.command_bus if hasattr(container, "app") else container.command_bus()
    )
    try:
        query_service: SchedulerDefinitionQueryService = (
            container.infra.scheduler_definition_query_service
            if hasattr(container, "app")
            else getattr(container, "scheduler_definition_query_service")()  # noqa: B009 -- atrybut spoza ContainerProtocol, direct access daje mypy attr-defined
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
