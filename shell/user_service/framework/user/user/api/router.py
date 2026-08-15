from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.dependencies import get_command_bus, get_query_bus
from shell.platform.framework.api.models.page import Page
from shell.platform.framework.api.principal import (
    Principal,
    get_principal,
    require_system_principal,
)
from shell.user_service.framework.user.user.api.change_user_request import ChangeUserRequest
from shell.user_service.framework.user.user.api.controller import UserController
from shell.user_service.framework.user.user.api.create_user_request import CreateUserRequest
from shell.user_service.framework.user.user.api.create_user_response import CreateUserResponse
from shell.user_service.framework.user.user.api.login_response import LoginResponse
from shell.user_service.framework.user.user.api.user_response import UserResponse

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_controller(
    command_bus: CommandBus = Depends(get_command_bus),
    query_bus: QueryBus = Depends(get_query_bus),
) -> UserController:
    return UserController(command_bus, query_bus)


@router.get("", response_model=Page[UserResponse])
async def list_users(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=100, ge=1, le=1000, alias="page_size"),
    principal: Principal = Depends(get_principal),
    controller: UserController = Depends(get_user_controller),
) -> Page[UserResponse]:
    return await controller.list_users(page=page, page_size=page_size, principal=principal)


@router.get("/by-email", response_model=LoginResponse)
async def get_user_by_email(
    email: str = Query(...),
    controller: UserController = Depends(get_user_controller),
) -> LoginResponse:
    return await controller.get_user_by_email(email)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: str,
    principal: Principal = Depends(get_principal),
    controller: UserController = Depends(get_user_controller),
) -> UserResponse:
    return await controller.get_user(user_id, principal=principal)


@router.post("/", response_model=CreateUserResponse, status_code=201)
async def create_user(
    body: CreateUserRequest,
    principal: Principal = Depends(require_system_principal),
    controller: UserController = Depends(get_user_controller),
) -> CreateUserResponse:
    del principal
    return await controller.create_user(body)


@router.put("/{user_id}", status_code=204)
async def change_user(
    user_id: str,
    body: ChangeUserRequest,
    principal: Principal = Depends(get_principal),
    controller: UserController = Depends(get_user_controller),
) -> None:
    await controller.change_user(user_id, body, principal=principal)


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: str,
    principal: Principal = Depends(get_principal),
    controller: UserController = Depends(get_user_controller),
) -> None:
    await controller.delete_user(user_id, principal=principal)
