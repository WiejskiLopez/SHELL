from __future__ import annotations

from fastapi import HTTPException

from shell.ingestion_service.application.ingestion.ingestion.commands.change_ingestion_command import (
    ChangeIngestionCommand,
)
from shell.ingestion_service.application.ingestion.ingestion.commands.create_ingestion_command import (
    CreateIngestionCommand,
)
from shell.ingestion_service.application.ingestion.ingestion.commands.delete_ingestion_command import (
    DeleteIngestionCommand,
)
from shell.ingestion_service.application.ingestion.ingestion.queries.get_ingestion_by_id_query import (
    GetIngestionByIdQuery,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.change_ingestion_request import (
    ChangeIngestionRequest as ApiChangeIngestionRequest,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.create_ingestion_request import (
    CreateIngestionRequest as ApiCreateIngestionRequest,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.create_ingestion_response import (
    CreateIngestionResponse as ApiCreateIngestionResponse,
)
from shell.ingestion_service.framework.ingestion.ingestion.api.ingestion_response import (
    IngestionResponse as ApiIngestionResponse,
)
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus


class IngestionController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
    ) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_ingestion(self, ingestion_id: str) -> ApiIngestionResponse:
        result = await self._query_bus.dispatch(GetIngestionByIdQuery(ingestion_id=ingestion_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"Ingestion '{ingestion_id}' not found")
        return ApiIngestionResponse(
            id=result.id,
            ingestion_data=str(result.ingestion_data),
            ingestion_context=str(result.ingestion_context),
            created_at=result.created_at,
            changed_at=result.changed_at,
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

    async def change_ingestion(self, ingestion_id: str, body: ApiChangeIngestionRequest) -> None:
        try:
            await self._command_bus.dispatch(ChangeIngestionCommand(ingestion_id=ingestion_id))
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
