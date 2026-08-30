from __future__ import annotations

from fastapi import APIRouter, Depends

from shell.ingestion_service.framework.ingestion.ingestion.api.change_ingestion_request import (
    ChangeIngestionRequest,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.controller import (
    IngestionController,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.create_ingestion_request import (
    CreateIngestionRequest,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.create_ingestion_response import (
    CreateIngestionResponse,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.ingestion_response import (
    IngestionResponse,
)
from shell.platform.application.bus.command_bus import (
    CommandBus,
)
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import get_command_bus, get_query_bus

router = APIRouter(prefix="/ingestions", tags=["Ingestions"])


def get_ingestion_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> IngestionController:
    return IngestionController(command_bus, query_bus)


@router.get("/{ingestion_id}", response_model=IngestionResponse)
async def get_ingestion(
    ingestion_id: str,
    controller: IngestionController = Depends(get_ingestion_controller),
) -> IngestionResponse:
    return await controller.get_ingestion(ingestion_id)


@router.post("/", response_model=CreateIngestionResponse, status_code=201)
async def create_ingestion(
    body: CreateIngestionRequest,
    controller: IngestionController = Depends(get_ingestion_controller),
) -> CreateIngestionResponse:
    return await controller.create_ingestion(body)


@router.put("/{ingestion_id}", status_code=204)
async def change_ingestion(
    ingestion_id: str,
    body: ChangeIngestionRequest,
    controller: IngestionController = Depends(get_ingestion_controller),
) -> None:
    await controller.change_ingestion(ingestion_id, body)


@router.delete("/{ingestion_id}", status_code=204)
async def delete_ingestion(
    ingestion_id: str,
    controller: IngestionController = Depends(get_ingestion_controller),
) -> None:
    await controller.delete_ingestion(ingestion_id)
