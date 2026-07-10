from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from shell.application.user.user.dto.user import (
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UserDto,
)
from shell.framework.user.user.api.controller import UserController
from shell.platform.framework.api.dependencies import get_core_container

if TYPE_CHECKING:
    from shell.domain.user.ports.user_acl import UserACL
    from shell.platform.application.bus.command_bus import CommandBus
    from shell.platform.bootstrap.container.core_container import CoreContainer

router = APIRouter(prefix="/users", tags=["users"])


def get_user_controller(
    container: CoreContainer = Depends(get_core_container),
) -> UserController:
    _user_acl: UserACL | None = getattr(container.infra, "user_acl_factory", None)
    if _user_acl is None:
        raise HTTPException(status_code=501, detail="User ACL not implemented")
    command_bus: CommandBus = container.app.buses.command_bus()  # type: ignore[attr-defined]
    return UserController(command_bus, _user_acl)


@router.get("/{user_id}", response_model=UserDto)
async def get_user(
    user_id: str,
    controller: UserController = Depends(get_user_controller),
) -> UserDto:
    return await controller.get_user(user_id)


@router.post("/", response_model=CreateUserResponse, status_code=201)
async def create_user(
    body: CreateUserRequest,
    controller: UserController = Depends(get_user_controller),
) -> CreateUserResponse:
    return await controller.create_user(body)


@router.put("/{user_id}", status_code=204)
async def update_user(
    user_id: str,
    body: UpdateUserRequest,
    controller: UserController = Depends(get_user_controller),
) -> None:
    await controller.update_user(user_id, body)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    controller: UserController = Depends(get_user_controller),
) -> None:
    await controller.delete_user(user_id)
