from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class UserEmail(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value:
            raise ValueError("UserEmail cannot be empty")
        if "@" not in self.value:
            raise ValueError(f"UserEmail must contain '@', got: {self.value!r}")

    def __str__(self) -> str:
        return self.value
