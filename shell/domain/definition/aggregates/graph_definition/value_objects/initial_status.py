from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class InitialStatus(ValueObject):
    value: str

    def __str__(self) -> str:
        return self.value
