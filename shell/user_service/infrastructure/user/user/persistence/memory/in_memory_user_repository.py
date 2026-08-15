from __future__ import annotations

from shell.platform.infrastructure.persistence.in_memory_repository import InMemoryRepository
from shell.user_service.domain.user.aggregates.user.repositories.user_repository import (
    UserRepository,
)
from shell.user_service.domain.user.aggregates.user.user import User
from shell.user_service.domain.user.value_objects.user_id import UserId


class InMemoryUserRepository(InMemoryRepository[User, UserId], UserRepository):
    pass
