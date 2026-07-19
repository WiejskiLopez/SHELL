from __future__ import annotations

from fastapi import HTTPException

from shell.application.user.user.commands.create_user_command import CreateUserCommand
from shell.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.application.user.user.commands.update_user_command import UpdateUserCommand
from shell.domain.user.aggregates.user.user import User
from shell.domain.user.ports.user_acl import UserACL
from shell.domain.user.value_objects.user_id import UserId
from shell.framework.user.user.api.create_user_request import (
    CreateUserRequest as ApiCreateUserRequest,
)
from shell.framework.user.user.api.create_user_response import (
    CreateUserResponse as ApiCreateUserResponse,
)
from shell.framework.user.user.api.update_user_request import (
    UpdateUserRequest as ApiUpdateUserRequest,
)
from shell.framework.user.user.api.user_response import UserResponse as ApiUserResponse
from shell.platform.application.bus.command_bus import CommandBus


def _user_to_response(user: User) -> ApiUserResponse:
    return ApiUserResponse(
        id=user.id.value,
        email=user.email.value,
        status=user.status.value,
        created_at=user.created_at.value,
        updated_at=user.updated_at.value,
        deleted_at=user.deleted_at.value,
    )


class UserController:
    __slots__ = ("_command_bus", "_user_acl")

    def __init__(self, command_bus: CommandBus, user_acl: UserACL) -> None:
        self._command_bus = command_bus
        self._user_acl = user_acl

    async def get_user(self, user_id: str) -> ApiUserResponse:
        result = await self._user_acl.get_user(UserId(user_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
        if not isinstance(result, User):
            raise HTTPException(status_code=500, detail="Unexpected user data format")
        return _user_to_response(result)

    async def create_user(self, body: ApiCreateUserRequest) -> ApiCreateUserResponse:
        user_id = await self._command_bus.dispatch(CreateUserCommand(email=body.email))
        return ApiCreateUserResponse(id=user_id)

    async def update_user(self, user_id: str, body: ApiUpdateUserRequest) -> None:
        try:
            await self._command_bus.dispatch(UpdateUserCommand(user_id=user_id, email=body.email))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_user(self, user_id: str) -> None:
        try:
            await self._command_bus.dispatch(DeleteUserCommand(user_id=user_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
