from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class Autopilot(ValueObject):
    value: bool

    def __str__(self) -> str:
        return str(self.value)
