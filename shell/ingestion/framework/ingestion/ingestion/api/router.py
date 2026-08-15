from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from shell.ingestion.framework.ingestion.ingestion.api.controller import (
    IngestionController,
)
from shell.ingestion.framework.ingestion.ingestion.api.create_ingestion_request import (
    CreateIngestionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.ingestion.framework.ingestion.ingestion.api.create_ingestion_response import (
    CreateIngestionResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.ingestion.framework.ingestion.ingestion.api.ingestion_response import (
    IngestionResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.ingestion.framework.ingestion.ingestion.api.update_ingestion_request import (
    UpdateIngestionRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.platform.application.bus.command_bus import (
    CommandBus,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.platform.framework.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.ingestion.application.ingestion.ingestion.ports.queries.ingestion_query_service import (
        IngestionQueryService,
    )
    from shell.platform.framework.api.dependencies import ContainerProtocol

router = APIRouter(prefix="/ingestions", tags=["Ingestions"])


def get_ingestion_controller(
    container: ContainerProtocol = Depends(get_core_container),
) -> IngestionController:
    try:
        _query_service: IngestionQueryService = (
            container.infra.ingestion_query_service
            if hasattr(container, "app")
            else getattr(container, "ingestion_query_service")()  # noqa: B009 -- atrybut spoza ContainerProtocol, direct access daje mypy attr-defined
        )
    except Exception:
        raise HTTPException(
            status_code=501, detail="Ingestion query service not implemented"
        ) from None
    command_bus: CommandBus = (
        container.app.buses.command_bus if hasattr(container, "app") else container.command_bus()
    )
    return IngestionController(command_bus, _query_service)


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
async def update_ingestion(
    ingestion_id: str,
    body: UpdateIngestionRequest,
    controller: IngestionController = Depends(get_ingestion_controller),
) -> None:
    await controller.update_ingestion(ingestion_id, body)


@router.delete("/{ingestion_id}", status_code=204)
async def delete_ingestion(
    ingestion_id: str,
    controller: IngestionController = Depends(get_ingestion_controller),
) -> None:
    await controller.delete_ingestion(ingestion_id)
