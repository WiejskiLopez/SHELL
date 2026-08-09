from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from shell.domain.user.aggregates.user.user import User
    from shell.domain.user.value_objects.user_email import UserEmail


class UserQueryProvider(Protocol):
    """Read-only lookup of a User by email — consumed by AuthSession aggregate."""

    async def get_by_email(self, email: UserEmail) -> User | None: ...
