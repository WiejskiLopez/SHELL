from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.ingestion.application.ingestion.ingestion.commands.create_ingestion_command import (
    CreateIngestionCommand,
)
from shell.ingestion.application.ingestion.ingestion.commands.delete_ingestion_command import (
    DeleteIngestionCommand,
)
from shell.ingestion.application.ingestion.ingestion.commands.update_ingestion_command import (
    UpdateIngestionCommand,
)
from shell.ingestion.framework.ingestion.ingestion.api.create_ingestion_request import (
    CreateIngestionRequest as ApiCreateIngestionRequest,
)
from shell.ingestion.framework.ingestion.ingestion.api.create_ingestion_response import (
    CreateIngestionResponse as ApiCreateIngestionResponse,
)
from shell.ingestion.framework.ingestion.ingestion.api.ingestion_response import (
    IngestionResponse as ApiIngestionResponse,
)
from shell.ingestion.framework.ingestion.ingestion.api.update_ingestion_request import (
    UpdateIngestionRequest as ApiUpdateIngestionRequest,
)
from shell.platform.application.bus.command_bus import CommandBus

if TYPE_CHECKING:
    from shell.ingestion.application.ingestion.ingestion.ports.queries.ingestion_query_service import (
        IngestionQueryService,
    )


class IngestionController:
    __slots__ = ("_command_bus", "_query_service")

    def __init__(
        self,
        command_bus: CommandBus,
        query_service: IngestionQueryService,
    ) -> None:
        self._command_bus = command_bus
        self._query_service = query_service

    async def get_ingestion(self, ingestion_id: str) -> ApiIngestionResponse:
        result = await self._query_service.get_by_id(ingestion_id)
        if result is None:
            raise HTTPException(status_code=404, detail=f"Ingestion '{ingestion_id}' not found")
        return ApiIngestionResponse(
            id=result.id,
            ingestion_data=str(result.ingestion_data),
            ingestion_context=str(result.ingestion_context),
            created_at=result.created_at,
            updated_at=result.updated_at,
            deleted_at=result.deleted_at,
        )

    async def create_ingestion(self, body: ApiCreateIngestionRequest) -> ApiCreateIngestionResponse:
        ingestion_id = await self._command_bus.dispatch(
            CreateIngestionCommand(
                ingestion_data=str(body.ingestion_data),
                ingestion_context=str(body.ingestion_context),
            )
        )
        return ApiCreateIngestionResponse(id=ingestion_id)

    async def update_ingestion(self, ingestion_id: str, body: ApiUpdateIngestionRequest) -> None:
        try:
            await self._command_bus.dispatch(UpdateIngestionCommand(ingestion_id=ingestion_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_ingestion(self, ingestion_id: str) -> None:
        try:
            await self._command_bus.dispatch(DeleteIngestionCommand(ingestion_id=ingestion_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
