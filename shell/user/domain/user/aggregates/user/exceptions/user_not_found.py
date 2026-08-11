from __future__ import annotations

from shell.platform.domain.exceptions.domain_error import DomainError


class UserNotFound(DomainError):
    def __init__(self, user_id: str) -> None:
        super().__init__(f"User not found: {user_id!r}")
