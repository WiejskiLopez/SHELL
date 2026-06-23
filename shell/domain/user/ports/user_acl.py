from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user.user import User
    from shell.domain.user.value_objects.user_id import UserId


class UserACL(Protocol):
    async def get_user(self, user_id: UserId) -> User: ...
