from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChangeUserCommand:
    user_id: str
    email: str

    def __post_init__(self) -> None:
        if not self.user_id:
            raise ValueError("user_id cannot be empty")
        if not self.email:
            raise ValueError("email cannot be empty")
