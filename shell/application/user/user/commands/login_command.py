from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LoginCommand:
    email: str

    def __post_init__(self) -> None:
        if not self.email:
            raise ValueError("email cannot be empty")
