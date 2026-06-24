from __future__ import annotations

import copy
from typing import TYPE_CHECKING

from shell.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.domain.user.value_objects.user_id import UserId

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user.user import User


class InMemoryUserRepository(UserRepository):
    def __init__(self) -> None:
        self._store: dict[str, User] = {}

    async def get_by_id(self, user_id: UserId) -> User | None:
        user = self._store.get(user_id.value)
        return copy.deepcopy(user) if user is not None else None

    async def save(self, user: User) -> None:
        self._store[user.id.value] = copy.deepcopy(user)
