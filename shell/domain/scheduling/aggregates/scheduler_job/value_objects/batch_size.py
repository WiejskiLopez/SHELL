from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class BatchSize(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 1:
            raise ValueError("BatchSize must be at least 1")

    def __str__(self) -> str:
        return str(self.value)
