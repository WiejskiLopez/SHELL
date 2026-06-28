from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class IntervalSeconds(ValueObject):
    value: float

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("IntervalSeconds cannot be negative")

    def __str__(self) -> str:
        return str(self.value)
