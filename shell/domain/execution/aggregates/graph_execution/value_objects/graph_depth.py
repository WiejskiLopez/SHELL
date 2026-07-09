from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class GraphDepth(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError(f"GraphDepth must be >= 0, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)
