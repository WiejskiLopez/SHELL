from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from shell.framework.messaging.message_router.api.controller import MessageRouterController
from shell.framework.messaging.message_router.api.create_message_router_request import (
    CreateMessageRouterRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.framework.messaging.message_router.api.create_message_router_response import (
    CreateMessageRouterResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.framework.messaging.message_router.api.message_router_response import (
    MessageRouterResponse,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.framework.messaging.message_router.api.update_message_router_request import (
    UpdateMessageRouterRequest,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.platform.application.bus.command_bus import (
    CommandBus,  # noqa: TC001 -- used at runtime for FastAPI
)
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.application.messaging.message_router.ports.queries.message_router_query_service import (
        MessageRouterQueryService,
    )

router = APIRouter(prefix="/message-routers", tags=["MessageRouters"])


def get_message_router_controller(
    container: CoreContainer = Depends(get_core_container),
) -> MessageRouterController:
    try:
        _query_service: MessageRouterQueryService = container.infra.message_router_query_service  # type: ignore[assignment]
    except Exception:
        raise HTTPException(
            status_code=501, detail="MessageRouter query service not implemented"
        ) from None
    command_bus: CommandBus = container.app.buses.command_bus
    return MessageRouterController(command_bus, _query_service)


@router.get("/{message_router_id}", response_model=MessageRouterResponse)
async def get_message_router(
    message_router_id: str,
    controller: MessageRouterController = Depends(get_message_router_controller),
) -> MessageRouterResponse:
    return await controller.get_message_router(message_router_id)


@router.post("/", response_model=CreateMessageRouterResponse, status_code=201)
async def create_message_router(
    body: CreateMessageRouterRequest,
    controller: MessageRouterController = Depends(get_message_router_controller),
) -> CreateMessageRouterResponse:
    return await controller.create_message_router(body)


@router.put("/{message_router_id}", status_code=204)
async def update_message_router(
    message_router_id: str,
    body: UpdateMessageRouterRequest,
    controller: MessageRouterController = Depends(get_message_router_controller),
) -> None:
    await controller.update_message_router(message_router_id, body)


@router.delete("/{message_router_id}", status_code=204)
async def delete_message_router(
    message_router_id: str,
    controller: MessageRouterController = Depends(get_message_router_controller),
) -> None:
    await controller.delete_message_router(message_router_id)
