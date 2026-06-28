from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class NoAskUser(ValueObject):
    value: bool

    def __str__(self) -> str:
        return str(self.value)
