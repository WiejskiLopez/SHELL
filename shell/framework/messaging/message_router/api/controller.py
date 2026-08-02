from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.messaging.message_router.commands.create_message_router_command import (
    CreateMessageRouterCommand,
)
from shell.application.messaging.message_router.commands.delete_message_router_command import (
    DeleteMessageRouterCommand,
)
from shell.application.messaging.message_router.commands.update_message_router_command import (
    UpdateMessageRouterCommand,
)
from shell.domain.messaging.aggregates.message_router.value_objects.message_router_id import (
    MessageRouterId,
)
from shell.framework.messaging.message_router.api.create_message_router_request import (
    CreateMessageRouterRequest as ApiCreateMessageRouterRequest,
)
from shell.framework.messaging.message_router.api.create_message_router_response import (
    CreateMessageRouterResponse as ApiCreateMessageRouterResponse,
)
from shell.framework.messaging.message_router.api.message_router_response import (
    MessageRouterResponse as ApiMessageRouterResponse,
)
from shell.framework.messaging.message_router.api.update_message_router_request import (
    UpdateMessageRouterRequest as ApiUpdateMessageRouterRequest,
)
from shell.platform.application.bus.command_bus import CommandBus

if TYPE_CHECKING:
    from shell.application.messaging.message_router.ports.queries.message_router_query_service import (
        MessageRouterQueryService,
    )


class MessageRouterController:
    __slots__ = ("_command_bus", "_query_service")

    def __init__(
        self,
        command_bus: CommandBus,
        query_service: MessageRouterQueryService,
    ) -> None:
        self._command_bus = command_bus
        self._query_service = query_service

    async def get_message_router(self, message_router_id: str) -> ApiMessageRouterResponse:
        result = await self._query_service.get_by_id(MessageRouterId(message_router_id))
        if result is None:
            raise HTTPException(
                status_code=404, detail=f"MessageRouter '{message_router_id}' not found"
            )
        return ApiMessageRouterResponse(
            id=result.id,
            message_data=str(result.message_data),
            message_context=str(result.message_context),
            created_at=result.created_at,
            updated_at=result.updated_at,
            deleted_at=result.deleted_at,
        )

    async def create_message_router(
        self, body: ApiCreateMessageRouterRequest
    ) -> ApiCreateMessageRouterResponse:
        message_router_id = await self._command_bus.dispatch(
            CreateMessageRouterCommand(
                message_data=str(body.message_data),
                message_context=str(body.message_context),
            )
        )
        return ApiCreateMessageRouterResponse(id=message_router_id)

    async def update_message_router(
        self, message_router_id: str, body: ApiUpdateMessageRouterRequest
    ) -> None:
        try:
            await self._command_bus.dispatch(
                UpdateMessageRouterCommand(message_router_id=message_router_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_message_router(self, message_router_id: str) -> None:
        try:
            await self._command_bus.dispatch(
                DeleteMessageRouterCommand(message_router_id=message_router_id)
            )
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
