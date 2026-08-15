from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import HTTPException

from shell.platform.application.bus.command_bus import CommandBus
from shell.platform.application.bus.query_bus import QueryBus
from shell.platform.framework.api.models.page import Page
from shell.platform.framework.api.principal import Principal, PrincipalKind
from shell.user_service.application.user.user.commands.change_user_command import ChangeUserCommand
from shell.user_service.application.user.user.commands.create_user_command import CreateUserCommand
from shell.user_service.application.user.user.commands.delete_user_command import DeleteUserCommand
from shell.user_service.application.user.user.queries.get_user_by_email_query import (
    GetUserByEmailQuery,
)
from shell.user_service.application.user.user.queries.get_user_by_id_query import GetUserByIdQuery
from shell.user_service.application.user.user.queries.list_users_query import ListUsersQuery
from shell.user_service.framework.user.user.api.change_user_request import (
    ChangeUserRequest as ApiChangeUserRequest,
)
from shell.user_service.framework.user.user.api.create_user_request import (
    CreateUserRequest as ApiCreateUserRequest,
)
from shell.user_service.framework.user.user.api.create_user_response import (
    CreateUserResponse as ApiCreateUserResponse,
)
from shell.user_service.framework.user.user.api.login_response import (
    LoginResponse as ApiLoginResponse,
)
from shell.user_service.framework.user.user.api.user_response import UserResponse as ApiUserResponse

if TYPE_CHECKING:
    from shell.user_service.application.user.user.dto.user import UserDto


def _dto_to_response(dto: UserDto) -> ApiUserResponse:
    return ApiUserResponse(
        id=dto.id,
        email=dto.email,
        status=dto.status,
        created_at=dto.created_at,
        changed_at=dto.changed_at,
        deleted_at=dto.deleted_at,
    )


class UserController:
    __slots__ = ("_command_bus", "_query_bus")

    def __init__(
        self,
        command_bus: CommandBus,
        query_bus: QueryBus,
    ) -> None:
        self._command_bus = command_bus
        self._query_bus = query_bus

    async def get_user(self, user_id: str, principal: Principal) -> ApiUserResponse:
        self._require_access(user_id, principal)
        result = await self._query_bus.dispatch(GetUserByIdQuery(user_id=user_id))
        if result is None:
            raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
        return _dto_to_response(result)

    async def list_users(
        self, page: int = 1, page_size: int = 100, principal: Principal | None = None
    ) -> Page[ApiUserResponse]:
        if principal is None:
            raise HTTPException(status_code=401, detail="Missing or invalid authentication")
        dtos, total = await self._query_bus.dispatch(ListUsersQuery(page=page, page_size=page_size))
        items = [_dto_to_response(d) for d in dtos]
        has_more = (page * page_size) < total
        return Page(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            has_more=has_more,
        )

    async def create_user(self, body: ApiCreateUserRequest) -> ApiCreateUserResponse:
        user_id = await self._command_bus.dispatch(CreateUserCommand(email=body.email))
        return ApiCreateUserResponse(id=user_id)

    async def get_user_by_email(self, email: str) -> ApiLoginResponse:
        result = await self._query_bus.dispatch(GetUserByEmailQuery(email=email))
        if result is None:
            raise HTTPException(status_code=404, detail=f"User with email '{email}' not found")
        return ApiLoginResponse(id=result.id)

    async def change_user(
        self, user_id: str, body: ApiChangeUserRequest, principal: Principal
    ) -> None:
        try:
            self._require_access(user_id, principal)
            await self._command_bus.dispatch(ChangeUserCommand(user_id=user_id, email=body.email))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    async def delete_user(self, user_id: str, principal: Principal) -> None:
        try:
            self._require_access(user_id, principal)
            await self._command_bus.dispatch(DeleteUserCommand(user_id=user_id))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    @staticmethod
    def _require_access(user_id: str, principal: Principal) -> None:
        if principal.kind == PrincipalKind.SYSTEM or principal.subject_id == user_id:
            return
        raise HTTPException(status_code=404, detail=f"User '{user_id}' not found")
