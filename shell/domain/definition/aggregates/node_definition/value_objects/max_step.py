from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class MaxStep(ValueObject):
    value: int | None

    def __post_init__(self) -> None:
        if self.value is not None and self.value < 0:
            raise DomainError("MaxStep must be >= 0")

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def of(cls, value: int | None) -> Self:
        return cls(value)
