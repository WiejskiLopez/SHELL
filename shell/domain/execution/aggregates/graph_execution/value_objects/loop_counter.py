from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class LoopCounter(ValueObject):
    transition_id: str
    current_iteration: int = 0
    max_loop_count: int = 0

    def __post_init__(self) -> None:
        if self.current_iteration < 0:
            raise ValueError("current_iteration cannot be negative")
        if self.max_loop_count < 0:
            raise ValueError("max_loop_count cannot be negative")

    @property
    def is_exhausted(self) -> bool:
        return self.max_loop_count > 0 and self.current_iteration >= self.max_loop_count

    def increment(self) -> LoopCounter:
        return LoopCounter(
            transition_id=self.transition_id,
            current_iteration=self.current_iteration + 1,
            max_loop_count=self.max_loop_count,
        )

    def __str__(self) -> str:
        return f"LoopCounter({self.transition_id}, {self.current_iteration}/{self.max_loop_count})"
