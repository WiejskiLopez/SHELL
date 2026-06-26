from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base import ValueObject


@dataclass(frozen=True, slots=True)
class RemainingRetries(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("RemainingRetries cannot be negative")
