from __future__ import annotations

from shell.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.domain.user.aggregates.user.user import User
from shell.domain.user.value_objects.user_id import UserId
from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository


class InMemoryUserRepository(InMemoryRepository[User, UserId], UserRepository):
    pass
