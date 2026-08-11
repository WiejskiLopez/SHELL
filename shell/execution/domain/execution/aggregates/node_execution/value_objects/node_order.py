from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject
from shell.platform.domain.exceptions.domain_error import DomainError


@dataclass(frozen=True, slots=True)
class NodeOrder(ValueObject):
    value: int

    def __post_init__(self) -> None:
        if self.value < 0:
            raise DomainError(f"NodeOrder must be >= 0, got {self.value}")

    def __str__(self) -> str:
        return str(self.value)
