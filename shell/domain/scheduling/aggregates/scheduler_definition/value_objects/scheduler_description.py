from __future__ import annotations

from dataclasses import dataclass

from shell.platform.domain.base.value_object import ValueObject


@dataclass(frozen=True, slots=True)
class SchedulerDescription(ValueObject):
    value: str

    def __str__(self) -> str:
        return self.value

    @classmethod
    def empty(cls) -> SchedulerDescription:
        return cls("")
