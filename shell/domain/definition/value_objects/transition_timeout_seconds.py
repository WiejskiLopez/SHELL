from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class TransitionTimeoutSeconds(ValueObject):
    value: int | None

    def __post_init__(self) -> None:
        if self.value is not None and self.value < 0:
            raise ValueError("TransitionTimeoutSeconds must be >= 0")

    def __str__(self) -> str:
        return str(self.value)
