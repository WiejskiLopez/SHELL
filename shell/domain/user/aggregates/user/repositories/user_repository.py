from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user.user import User
    from shell.domain.user.value_objects.user_id import UserId


class UserRepository(Protocol):
    async def get_by_id(self, user_id: UserId) -> User | None: ...
    async def save(self, user: User) -> None: ...
    async def delete(self, id: UserId) -> None: ...
    async def exists(self, id: UserId) -> bool: ...
    