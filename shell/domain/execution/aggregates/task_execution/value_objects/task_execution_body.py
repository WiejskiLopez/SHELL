"""TaskExecutionBody value object — text content of a task definition."""

from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class TaskExecutionBody(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value or not self.value.strip():
            raise ValueError("TaskExecutionBody cannot be empty")

    def __str__(self) -> str:
        return self.value
