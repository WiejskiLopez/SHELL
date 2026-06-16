"""TaskBody value object — text content of a task definition."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskBody:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskBody cannot be empty")

    def __str__(self) -> str:
        return self.value
