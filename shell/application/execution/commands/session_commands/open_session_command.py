from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class OpenSessionCommand:
    goal: str

    def __post_init__(self) -> None:
        if not self.goal:
            raise ValueError("goal cannot be empty")
