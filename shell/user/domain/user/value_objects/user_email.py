from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class UserEmail(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise DomainError("UserEmail cannot be empty")
        if "@" not in self.value:
            raise DomainError(f"UserEmail must contain '@', got: {self.value!r}")

    def __str__(self) -> str:
        return self.value
