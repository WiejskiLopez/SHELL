from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.user_service.application.user.user.dto.user import UserDto


class UserQueryService(Protocol):
    async def get_by_id(self, user_id: str) -> UserDto | None: ...
    async def get_by_email(self, email: str) -> UserDto | None: ...

    async def list_all(
        self, *, page: int = 1, page_size: int = 100
    ) -> tuple[list[UserDto], int]: ...
