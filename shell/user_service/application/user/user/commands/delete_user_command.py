from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DeleteUserCommand:
    user_id: str

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
