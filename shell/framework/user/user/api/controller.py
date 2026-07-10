from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.application.user.user.commands.create_user_command import CreateUserCommand
from shell.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.application.user.user.commands.update_user_command import UpdateUserCommand
from shell.application.user.user.dto.user import (
    CreateUserRequest,
    CreateUserResponse,
    UpdateUserRequest,
    UserDto,
)
from shell.domain.user.aggregates.user.user import User
from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.domain.user.ports.user_acl import UserACL
    from shell.platform.application.bus.command_bus import CommandBus


class UserController:
    __slots__ = ("_command_bus", "_user_acl")

    def __init__(self, command_bus: CommandBus, user_acl: UserACL) -> None:
        self._command_bus = command_bus
        self._user_acl = user_acl

    async def get_user(self, user_id: str) -> UserDto:
        result = await self._user_acl.get_user(UserId(user_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
        if not isinstance(result, User):
            raise HTTPException(status_code=500, detail="Unexpected user data format")
        return UserDto(
            id=result.id.value,
            email=result.email.value,
            status=result.status.value,
            created_at=result.created_at.value,  # type: ignore[union-attr]
            updated_at=result.updated_at.value if result.updated_at else None,  # type: ignore[arg-type]
            deleted_at=result.deleted_at.value if result.deleted_at else None,
        )

    async def create_user(self, body: CreateUserRequest) -> CreateUserResponse:
        user_id = await self._command_bus.dispatch(CreateUserCommand(email=body.email))
        return CreateUserResponse(id=user_id)

    async def update_user(self, user_id: str, body: UpdateUserRequest) -> None:
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
