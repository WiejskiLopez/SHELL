"""Enabled value object — boolean domain wrapper."""
from __future__ import annotations
from dataclasses import dataclass
from shell.domain.platform.base.value_object import ValueObject

@dataclass(frozen=True, slots=True)
class Enabled(ValueObject):
    value: bool

    def __str__(self) -> str:
        return str(self.value)

    @classmethod
    def yes(cls) -> Enabled:
        return cls(True)

    @classmethod
    def no(cls) -> Enabled:
        return cls(False)
