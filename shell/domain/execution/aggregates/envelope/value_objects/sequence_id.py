from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SequenceId(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("SequenceId cannot be negative")

    def __str__(self) -> str:
        return str(self.value)

    def __ge__(self, other: int) -> bool:
        return self.value >= other

    def __lt__(self, other: int) -> bool:
        return self.value < other
