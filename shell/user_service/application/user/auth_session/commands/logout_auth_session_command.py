from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LogoutAuthSessionCommand:
    token: str

    def __post_init__(self) -> None:
        if not self.token:
            raise ValueError("token cannot be empty")
