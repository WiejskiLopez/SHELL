"""TaskExecutionName value object."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TaskExecutionName:
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskExecutionName cannot be empty")
        if len(self.value) > 255:
            raise ValueError("TaskExecutionName cannot exceed 255 characters")

    def __str__(self) -> str:
        return self.value
