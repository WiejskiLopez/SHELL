from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChangeSessionCommand:
    session_id: str

    def __post_init__(self) -> None:
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
