from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from shell.domain.user.ports.user_acl import UserACL
from shell.framework.user.user.api.controller import UserController
from shell.framework.user.user.api.create_user_request import CreateUserRequest
from shell.framework.user.user.api.create_user_response import CreateUserResponse
from shell.framework.user.user.api.update_user_request import UpdateUserRequest
from shell.framework.user.user.api.user_response import UserResponse
from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.bootstrap.container.core_container import CoreContainer
from shell.platform.framework.api.dependencies import get_core_container

router = APIRouter(prefix="/users", tags=["users"])


def get_user_controller(
    container: CoreContainer = Depends(get_core_container),
) -> UserController:
    try:
        _user_acl: UserACL = container.infra.user_acl_factory()
    except Exception:
        raise HTTPException(status_code=501, detail="User ACL not implemented") from None
    command_bus: CommandBus = container.app.buses.command_bus()  # type: ignore[attr-defined]
    return UserController(command_bus, _user_acl)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    controller: UserController = Depends(get_user_controller),
) -> UserResponse:
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
