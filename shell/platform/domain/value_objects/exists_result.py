from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class ExistsResult(ValueObject):
    value: bool

    def __bool__(self) -> bool:
        return self.value

    def __str__(self) -> str:
        return str(self.value)
