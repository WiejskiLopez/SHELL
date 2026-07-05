from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    user_id: str
    code: str

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        if not self.code:
            raise ValueError("code cannot be empty")
