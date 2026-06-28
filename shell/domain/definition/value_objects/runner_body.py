from __future__ import annotations

from dataclasses import dataclass

from shell.domain.platform.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class RunnerBody(ValueObject):
    value: dict[str, object]

    def __str__(self) -> str:
        return str(self.value)
