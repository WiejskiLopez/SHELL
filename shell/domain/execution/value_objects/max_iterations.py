from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base import ValueObject


@dataclass(frozen=True, slots=True)
class MaxIterations(ValueObject):
    value: int | None

    def __post_init__(self) -> None:
        if self.value is not None and self.value < 0:
            raise ValueError("MaxIterations cannot be negative")
