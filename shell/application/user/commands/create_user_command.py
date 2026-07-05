from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CreateUserCommand:
    code: str

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("code cannot be empty")
