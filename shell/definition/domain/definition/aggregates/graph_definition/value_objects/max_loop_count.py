from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class MaxLoopCount(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise DomainError("MaxLoopCount must be >= 0")

    def __str__(self) -> str:
        return str(self.value)
