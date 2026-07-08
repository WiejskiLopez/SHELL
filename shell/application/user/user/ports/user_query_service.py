from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.application.user.user.dto.user import UserDto


class UserQueryService(Protocol):
    async def get_by_id(self, user_id: str) -> UserDto | None: ...
